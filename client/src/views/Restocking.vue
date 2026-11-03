<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-header">
          <label for="budget-slider" class="budget-label">{{ t('restocking.budget') }}</label>
          <div class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <input
          id="budget-slider"
          v-model.number="budget"
          type="range"
          min="0"
          :max="maxBudget"
          step="500"
          class="budget-slider"
        />
        <div class="budget-scale">
          <span>{{ formatCurrency(0, currentCurrency) }}</span>
          <span>{{ formatCurrency(maxBudget, currentCurrency) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.spend') }}</div>
          <div class="stat-value">{{ formatCurrencyWithDecimals(totalSpend, currentCurrency, 2) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatCurrencyWithDecimals(remainingBudget, currentCurrency, 2) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.orderLeadTime') }}</div>
          <div class="stat-value">{{ orderLeadTime === null ? '–' : t('restocking.days', { count: orderLeadTime }) }}</div>
        </div>
      </div>

      <div v-if="placedOrder" class="banner banner-success" role="status">
        <span>{{ t('restocking.orderPlaced', { orderNumber: placedOrder.order_number, days: placedOrder.lead_time_days }) }}</span>
        <router-link to="/orders" class="banner-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="submitError" class="banner banner-error" role="alert">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ shortfallItems.length === 0 ? t('restocking.nothingToRestock') : t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.shortfall') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recommendations" :key="row.sku">
                <td><strong>{{ row.sku }}</strong></td>
                <td>{{ row.item_name }}</td>
                <td>
                  <span :class="['badge', row.trend]">{{ t(`trends.${row.trend}`) }}</span>
                </td>
                <td class="num">{{ row.shortfall }}</td>
                <td class="num"><strong>{{ row.quantity }}</strong></td>
                <td class="num">{{ formatCurrencyWithDecimals(row.unit_cost, currentCurrency, 2) }}</td>
                <td class="num"><strong>{{ formatCurrencyWithDecimals(row.lineCost, currentCurrency, 2) }}</strong></td>
                <td class="num">{{ t('restocking.days', { count: row.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const TREND_ORDER = { increasing: 0, stable: 1, decreasing: 2 }
const BUDGET_ROUND_STEP = 5000

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(0)
    const submitting = ref(false)
    const submitError = ref(null)
    const placedOrder = ref(null)

    // Items where forecasted demand exceeds stock, sorted by restocking priority:
    // rising demand first, then larger unit shortfall
    const shortfallItems = computed(() => {
      return forecasts.value
        .map(f => ({ ...f, shortfall: f.forecasted_demand - f.quantity_on_hand }))
        .filter(f => f.shortfall > 0)
        .sort((a, b) => {
          const trendDiff = (TREND_ORDER[a.trend] ?? 3) - (TREND_ORDER[b.trend] ?? 3)
          return trendDiff !== 0 ? trendDiff : b.shortfall - a.shortfall
        })
    })

    // Slider max = cost of covering every shortfall, rounded up to the next 5,000
    const maxBudget = computed(() => {
      const total = shortfallItems.value.reduce((sum, f) => sum + f.shortfall * f.unit_cost, 0)
      if (total <= 0) return BUDGET_ROUND_STEP
      return Math.ceil(total / BUDGET_ROUND_STEP) * BUDGET_ROUND_STEP
    })

    const recommendations = computed(() => {
      const rows = []
      let remaining = budget.value

      // Greedy walk in priority order. The last affordable item gets a partial
      // quantity (whatever the remaining budget buys), and items that do not
      // fit at all are skipped, since a later, cheaper item may still fit.
      for (const item of shortfallItems.value) {
        const units = Math.min(item.shortfall, Math.floor(remaining / item.unit_cost))
        if (units <= 0) continue

        const lineCost = units * item.unit_cost
        rows.push({
          sku: item.item_sku,
          item_name: item.item_name,
          trend: item.trend,
          shortfall: item.shortfall,
          quantity: units,
          unit_cost: item.unit_cost,
          lineCost,
          lead_time_days: item.lead_time_days
        })
        remaining -= lineCost
      }
      return rows
    })

    const totalSpend = computed(() => recommendations.value.reduce((sum, r) => sum + r.lineCost, 0))
    const remainingBudget = computed(() => Math.max(0, budget.value - totalSpend.value))

    const orderLeadTime = computed(() => {
      if (recommendations.value.length === 0) return null
      return Math.max(...recommendations.value.map(r => r.lead_time_days))
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        // Start at roughly 25% of the range, snapped to the slider step
        budget.value = Math.round(maxBudget.value * 0.25 / 500) * 500
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (submitting.value || recommendations.value.length === 0) return

      submitting.value = true
      submitError.value = null
      placedOrder.value = null
      try {
        placedOrder.value = await api.createRestockingOrder({
          budget: budget.value,
          items: recommendations.value.map(r => ({ sku: r.sku, quantity: r.quantity }))
        })
      } catch (err) {
        submitError.value = err.response?.data?.detail || err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      currentCurrency,
      formatCurrency,
      formatCurrencyWithDecimals,
      loading,
      error,
      budget,
      maxBudget,
      shortfallItems,
      recommendations,
      totalSpend,
      remainingBudget,
      orderLeadTime,
      submitting,
      submitError,
      placedOrder,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
}

.budget-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.budget-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  accent-color: #0f172a;
  cursor: pointer;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.375rem;
  font-size: 0.813rem;
  color: #64748b;
}

.num {
  text-align: right;
}

.place-order-btn {
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  color: #64748b;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.875rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.banner-success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.banner-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.banner-link {
  color: #0f172a;
  font-weight: 600;
  white-space: nowrap;
}
</style>
