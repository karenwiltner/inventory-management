<template>
  <!-- Empty in flow: the sidebar and top bar are position: fixed. As the first grid item
       of .app this element is the spacer that reserves the sidebar column. -->
  <div class="sidebar-shell">
    <header v-if="isMobile" class="topbar">
      <button
        ref="hamburgerRef"
        type="button"
        class="icon-button"
        :aria-label="t('nav.openMenu')"
        :aria-expanded="drawerOpen"
        aria-controls="app-sidebar"
        @click="openDrawer"
      >
        <svg class="icon" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
          <path d="M3 5.5h14M3 10h14M3 14.5h14" />
        </svg>
      </button>
      <span class="topbar-title">{{ t('nav.companyName') }}</span>
    </header>

    <div
      v-if="isMobile && drawerOpen"
      class="drawer-backdrop"
      aria-hidden="true"
      @click="closeDrawer()"
    ></div>

    <div
      v-if="tabletExpanded"
      class="drawer-backdrop"
      aria-hidden="true"
      @click="collapseTablet(true)"
    ></div>

    <aside
      id="app-sidebar"
      ref="sidebarRef"
      class="sidebar"
      :class="{
        'is-collapsed': collapsedView,
        'is-mobile': isMobile,
        'is-open': drawerOpen,
        'is-overlay': tabletExpanded
      }"
    >
      <div class="sidebar-header">
        <div class="brand">
          <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
          <div class="brand-text" :class="{ 'visually-hidden': collapsedView }">
            <span class="brand-name">{{ t('nav.companyName') }}</span>
            <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
          </div>
        </div>
        <button
          v-if="isMobile"
          type="button"
          class="icon-button"
          :aria-label="t('nav.closeMenu')"
          @click="closeDrawer()"
        >
          <svg class="icon" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
            <path d="M5 5l10 10M15 5L5 15" />
          </svg>
        </button>
      </div>

      <!-- The only scroll area. The footer below sits outside it, because an overflow
           container would clip the dropdowns that open to the right of the sidebar. -->
      <div class="sidebar-scroll">
        <nav ref="navRef" :aria-label="t('nav.mainNavigation')">
          <div v-for="group in groups" :key="group.id" class="nav-group">
            <p
              :id="'nav-group-' + group.id"
              class="nav-group-heading"
              :class="{ 'visually-hidden': collapsedView }"
            >
              {{ t(group.headingKey) }}
            </p>
            <ul class="nav-list" :aria-labelledby="'nav-group-' + group.id">
              <li v-for="item in group.items" :key="item.to">
                <router-link
                  :to="item.to"
                  class="nav-link"
                  exact-active-class="is-active"
                  :title="collapsedView ? t(item.labelKey) : null"
                >
                  <svg class="icon" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
                    <path v-for="d in item.icon" :key="d" :d="d" />
                  </svg>
                  <span class="nav-label" :class="{ 'visually-hidden': collapsedView }">
                    {{ t(item.labelKey) }}
                  </span>
                </router-link>
              </li>
            </ul>
          </div>
        </nav>
      </div>

      <div class="sidebar-footer">
        <LanguageSwitcher :collapsed="collapsedView" />
        <ProfileMenu
          :collapsed="collapsedView"
          @show-profile-details="$emit('show-profile-details')"
          @show-tasks="$emit('show-tasks')"
        />
        <button
          v-if="!isMobile"
          ref="toggleRef"
          type="button"
          class="collapse-toggle"
          :aria-expanded="!collapsedView"
          :aria-label="collapsedView ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          :title="collapsedView ? t('nav.expandSidebar') : null"
          @click="onToggleClick"
        >
          <svg
            class="icon chevron"
            :class="{ 'chevron-flipped': collapsedView }"
            viewBox="0 0 20 20"
            aria-hidden="true"
            focusable="false"
          >
            <path d="M12.5 5l-5 5 5 5" />
          </svg>
          <span v-if="!collapsedView" class="nav-label" aria-hidden="true">
            {{ t('nav.collapseSidebar') }}
          </span>
        </button>
      </div>
    </aside>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

const STORAGE_KEY = 'app-sidebar-collapsed'
const MOBILE_QUERY = '(max-width: 767.98px)'
const TABLET_QUERY = '(min-width: 768px) and (max-width: 1023.98px)'
const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'

// Line icons, 20x20 grid. Stroke styling is set in CSS on .icon.
const groups = [
  {
    id: 'operations',
    headingKey: 'nav.groupOperations',
    items: [
      {
        to: '/',
        labelKey: 'nav.overview',
        icon: ['M3 3h5.5v5.5H3zM11.5 3H17v5.5h-5.5zM3 11.5h5.5V17H3zM11.5 11.5H17V17h-5.5z']
      },
      {
        to: '/inventory',
        labelKey: 'nav.inventory',
        icon: [
          'M10 2.5l6.5 3.25v8.5L10 17.5l-6.5-3.25v-8.5L10 2.5z',
          'M3.5 5.75L10 9l6.5-3.25',
          'M10 9v8.5'
        ]
      },
      {
        to: '/orders',
        labelKey: 'nav.orders',
        icon: [
          'M7 4H5.5A1.5 1.5 0 0 0 4 5.5v10A1.5 1.5 0 0 0 5.5 17h9a1.5 1.5 0 0 0 1.5-1.5v-10A1.5 1.5 0 0 0 14.5 4H13',
          'M7.5 2.5h5a.5.5 0 0 1 .5.5v1.5a.5.5 0 0 1-.5.5h-5a.5.5 0 0 1-.5-.5V3a.5.5 0 0 1 .5-.5z',
          'M7 9.5h6M7 13h4'
        ]
      },
      {
        to: '/restocking',
        labelKey: 'nav.restocking',
        icon: [
          'M16.5 10a6.5 6.5 0 0 1-11.3 4.4',
          'M3.5 10a6.5 6.5 0 0 1 11.3-4.4',
          'M15 2.5V6h-3.5',
          'M5 17.5V14h3.5'
        ]
      }
    ]
  },
  {
    id: 'insights',
    headingKey: 'nav.groupInsights',
    items: [
      {
        to: '/demand',
        labelKey: 'nav.demandForecast',
        icon: ['M3 14.5l5-5 3 3 6-6', 'M13 6.5h4v4']
      },
      {
        to: '/spending',
        labelKey: 'nav.finance',
        icon: [
          'M2.5 5.5h15v9h-15z',
          'M12 10a2 2 0 1 1-4 0 2 2 0 0 1 4 0z',
          'M5.5 10h.01M14.5 10h.01'
        ]
      },
      {
        to: '/reports',
        labelKey: 'nav.reports',
        icon: ['M3 17.5h14', 'M5.5 14V10', 'M10 14V5', 'M14.5 14V8']
      }
    ]
  }
]

const readCollapsed = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true'
  } catch {
    return false
  }
}

export default {
  name: 'AppSidebar',
  components: {
    LanguageSwitcher,
    ProfileMenu
  },
  emits: ['show-profile-details', 'show-tasks', 'update:collapsed'],
  setup(props, { emit }) {
    const { t } = useI18n()
    const route = useRoute()

    const isCollapsed = ref(readCollapsed())
    const isMobile = ref(false)
    const isTablet = ref(false)
    const drawerOpen = ref(false)
    // Tablet overlay state: deliberately separate from isCollapsed and never persisted,
    // so the tablet always starts as the rail and never touches the desktop preference.
    const tabletOpen = ref(false)

    const hamburgerRef = ref(null)
    const sidebarRef = ref(null)
    const navRef = ref(null)
    const toggleRef = ref(null)

    let mobileQuery = null
    let tabletQuery = null
    let scrollLocked = false
    let previousBodyOverflow = ''

    const tabletExpanded = computed(() => isTablet.value && tabletOpen.value)

    // Visual state of the aside and the footer widgets. The phone drawer is never
    // collapsed, the tablet is a rail unless the overlay is open, desktop follows the
    // stored preference.
    const collapsedView = computed(() => {
      if (isMobile.value) return false
      if (isTablet.value) return !tabletOpen.value
      return isCollapsed.value
    })

    // What App.vue uses for the grid column. Always true on tablet: the overlay floats
    // above the content, so the spacer column must stay at rail width to avoid a layout shift.
    const layoutCollapsed = computed(() => {
      if (isMobile.value) return false
      if (isTablet.value) return true
      return isCollapsed.value
    })

    const brandInitial = computed(() => t('nav.companyName').charAt(0).toUpperCase())

    const toggleCollapsed = () => {
      isCollapsed.value = !isCollapsed.value
      try {
        localStorage.setItem(STORAGE_KEY, String(isCollapsed.value))
      } catch {
        // Storage unavailable (private mode): the toggle still works for this session
      }
    }

    const setScrollLock = (locked) => {
      if (locked === scrollLocked) return
      scrollLocked = locked
      if (locked) {
        previousBodyOverflow = document.body.style.overflow
        document.body.style.overflow = 'hidden'
      } else {
        document.body.style.overflow = previousBodyOverflow
      }
    }

    const handleKeydown = (event) => {
      if (!drawerOpen.value) return

      if (event.key === 'Escape') {
        closeDrawer()
        return
      }

      // Keep Tab inside the drawer while it is open
      if (event.key === 'Tab' && sidebarRef.value) {
        const focusable = Array.from(sidebarRef.value.querySelectorAll(FOCUSABLE))
          .filter((el) => el.getClientRects().length > 0)
        if (focusable.length === 0) return

        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        const active = document.activeElement

        if (!sidebarRef.value.contains(active)) {
          event.preventDefault()
          first.focus()
        } else if (event.shiftKey && active === first) {
          event.preventDefault()
          last.focus()
        } else if (!event.shiftKey && active === last) {
          event.preventDefault()
          first.focus()
        }
      }
    }

    const openDrawer = () => {
      if (drawerOpen.value) return
      drawerOpen.value = true
      setScrollLock(true)
      document.addEventListener('keydown', handleKeydown)
      nextTick(() => {
        const target = navRef.value?.querySelector('a')
        if (target) target.focus()
      })
    }

    const closeDrawer = (restoreFocus = true) => {
      if (!drawerOpen.value) return
      drawerOpen.value = false
      setScrollLock(false)
      document.removeEventListener('keydown', handleKeydown)
      if (restoreFocus) {
        nextTick(() => {
          if (hamburgerRef.value) hamburgerRef.value.focus()
        })
      }
    }

    const handleTabletKeydown = (event) => {
      if (event.key === 'Escape') collapseTablet(true)
    }

    const collapseTablet = (restoreFocus = false) => {
      if (!tabletOpen.value) return
      tabletOpen.value = false
      if (restoreFocus) {
        nextTick(() => {
          if (toggleRef.value) toggleRef.value.focus()
        })
      }
    }

    const onToggleClick = () => {
      if (isTablet.value) {
        tabletOpen.value = !tabletOpen.value
      } else {
        toggleCollapsed()
      }
    }

    const handleMobileChange = (event) => {
      isMobile.value = event.matches
      // The hamburger is unmounted on desktop, so there is nothing to focus
      if (!event.matches) closeDrawer(false)
    }

    const handleTabletChange = (event) => {
      isTablet.value = event.matches
      if (!event.matches) collapseTablet()
    }

    watch(() => route.path, () => {
      closeDrawer()
      collapseTablet()
    })

    watch(layoutCollapsed, (value) => emit('update:collapsed', value))

    watch(tabletExpanded, (open) => {
      if (open) {
        document.addEventListener('keydown', handleTabletKeydown)
      } else {
        document.removeEventListener('keydown', handleTabletKeydown)
      }
    })

    onMounted(() => {
      mobileQuery = window.matchMedia(MOBILE_QUERY)
      tabletQuery = window.matchMedia(TABLET_QUERY)
      isMobile.value = mobileQuery.matches
      isTablet.value = tabletQuery.matches
      mobileQuery.addEventListener('change', handleMobileChange)
      tabletQuery.addEventListener('change', handleTabletChange)
      emit('update:collapsed', layoutCollapsed.value)
    })

    onBeforeUnmount(() => {
      if (mobileQuery) mobileQuery.removeEventListener('change', handleMobileChange)
      if (tabletQuery) tabletQuery.removeEventListener('change', handleTabletChange)
      document.removeEventListener('keydown', handleKeydown)
      document.removeEventListener('keydown', handleTabletKeydown)
      setScrollLock(false)
    })

    return {
      t,
      groups,
      isMobile,
      drawerOpen,
      tabletExpanded,
      collapsedView,
      brandInitial,
      hamburgerRef,
      sidebarRef,
      navRef,
      toggleRef,
      onToggleClick,
      collapseTablet,
      openDrawer,
      closeDrawer
    }
  }
}
</script>

<style scoped>
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}

.icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* Sidebar (desktop) */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-w);
  height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: var(--z-sidebar);
  transition: width var(--transition-base);
}

.sidebar.is-collapsed {
  width: var(--sidebar-w-collapsed);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-3);
  flex-shrink: 0;
}

.is-collapsed .sidebar-header {
  justify-content: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.brand-mark {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: var(--color-surface);
  font-size: var(--text-md);
  font-weight: 700;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name,
.brand-subtitle {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand-name {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.sidebar-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-2) var(--space-3);
}

.nav-group + .nav-group {
  margin-top: var(--space-4);
}

.is-collapsed .nav-group + .nav-group {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.nav-group-heading {
  padding: 0 var(--space-3);
  margin-bottom: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted);
}

.nav-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-link,
.collapse-toggle {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  height: 40px;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  text-decoration: none;
  text-align: left;
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.nav-link:hover,
.collapse-toggle:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.nav-link.is-active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

/* Indicator sits on the sidebar's own edge, so it is offset by the nav padding */
.nav-link.is-active::before {
  content: '';
  position: absolute;
  top: var(--space-2);
  bottom: var(--space-2);
  left: calc(-1 * var(--space-3));
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--color-primary);
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.is-collapsed .nav-link,
.is-collapsed .collapse-toggle {
  justify-content: center;
  padding: 0;
}

/* Footer is pinned and deliberately not an overflow container: dropdowns open
   sideways out of it and would be clipped otherwise. */
.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex-shrink: 0;
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.chevron {
  transition: transform var(--transition-base);
}

.chevron-flipped {
  transform: rotate(180deg);
}

/* Shared focus ring */
.nav-link:focus-visible,
.collapse-toggle:focus-visible,
.icon-button:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

/* Top bar and drawer (below 768px) */
.topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-3);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  z-index: var(--z-sidebar);
}

.topbar-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.icon-button {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.icon-button:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  z-index: var(--z-drawer-overlay);
}

/* Tablet: the expanded sidebar floats over the content (the grid column stays at rail width,
   so the fixed width change above never reflows the page). It sits above the backdrop. */
.sidebar.is-overlay {
  z-index: var(--z-drawer);
  box-shadow: var(--shadow-lg);
}

/* visibility keeps the closed drawer out of the tab order and the accessibility tree.
   It flips to hidden only after the slide-out finishes. */
.sidebar.is-mobile {
  z-index: var(--z-drawer);
  transform: translateX(-100%);
  visibility: hidden;
  transition: transform var(--transition-base), visibility 0s linear var(--transition-base);
}

.sidebar.is-mobile.is-open {
  transform: translateX(0);
  visibility: visible;
  box-shadow: var(--shadow-lg);
  transition: transform var(--transition-base), visibility 0s;
}
</style>
