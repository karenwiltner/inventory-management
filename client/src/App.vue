<template>
  <div class="app" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <AppSidebar
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
      @update:collapsed="sidebarCollapsed = $event"
    />
    <div class="app-content">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import AppSidebar from './components/AppSidebar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'

export default {
  name: 'App',
  components: {
    AppSidebar,
    FilterBar,
    ProfileDetailsModal,
    TasksModal
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const sidebarCollapsed = ref(false)
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      sidebarCollapsed,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Column 1 is the AppSidebar shell, an empty spacer (the sidebar itself is fixed).
   minmax(0, 1fr) lets the content column shrink below its min-content width, otherwise
   wide tables would push the whole page sideways. */
.app {
  display: grid;
  grid-template-columns: var(--sidebar-current-w, var(--sidebar-w)) minmax(0, 1fr);
  min-height: 100dvh;
  transition: grid-template-columns var(--transition-base);
}

.app.sidebar-collapsed {
  --sidebar-current-w: var(--sidebar-w-collapsed);
}

.app-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

/* Below 768px the sidebar is an off-canvas drawer and a fixed top bar takes its place,
   so the content starts below that bar. On tablets (768-1023px) the sidebar stays an icon
   rail and AppSidebar reports it as collapsed, so the two-column grid keeps 72px for it. */
@media (max-width: 767.98px) {
  /* The empty sidebar shell becomes its own zero-height row. 1fr on the content row keeps
     leftover min-height from being split onto the shell row. */
  .app {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto 1fr;
  }

  .app-content {
    padding-top: var(--topbar-h);
  }
}

@media (max-width: 767.98px) {
  .main-content {
    padding: var(--space-4);
  }
}

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.02em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

/* Hover changes shadow and border color only, so cards never shift the layout. */
.stat-card {
  background: var(--color-surface);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.2;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.stat-card.warning .stat-value {
  color: #ea580c;
}

.stat-card.success .stat-value {
  color: #059669;
}

.stat-card.danger .stat-value {
  color: #dc2626;
}

.stat-card.info .stat-value {
  color: var(--color-primary);
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
}

/* Negative margins pull the header to the card edges so its bottom border spans the full width. */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin: calc(-1 * var(--space-6)) calc(-1 * var(--space-6)) var(--space-6);
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.table-container {
  max-width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

thead {
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-3);
  font-weight: 600;
  color: #475569;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

td {
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-surface-muted);
  color: #334155;
  font-size: var(--text-base);
  line-height: 1.25rem;
}

tbody tr:last-child td {
  border-bottom: none;
}

tbody tr {
  transition: background-color var(--transition-fast);
}

tbody tr:hover {
  background: var(--color-bg);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: 9999px;
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1.25;
  white-space: nowrap;
}

.badge.success,
.badge.increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.warning,
.badge.medium {
  background: #ffedd5;
  color: #9a3412;
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: #fee2e2;
  color: #991b1b;
}

.badge.info,
.badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}

a:focus-visible,
button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
summary:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

/* A box-shadow ring looks odd around a range track, so use an outline there. */
input[type='range'] {
  accent-color: var(--color-primary);
}

input[type='range']:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  box-shadow: none;
}
</style>
