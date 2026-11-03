<template>
  <div class="language-switcher">
    <button
      type="button"
      class="language-button"
      :class="{ 'is-collapsed': collapsed }"
      :aria-expanded="isDropdownOpen"
      :title="collapsed ? localeName : null"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        class="globe-icon"
        aria-hidden="true"
        focusable="false"
      >
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.75"/>
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.75"/>
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.75"/>
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.75"/>
      </svg>
      <span class="language-label" :class="{ 'visually-hidden': collapsed }">{{ localeName }}</span>
      <svg
        v-if="!collapsed"
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
        focusable="false"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        type="button"
        class="dropdown-item"
        :class="{ active: currentLocale === locale }"
        @mousedown.prevent="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg
          v-if="currentLocale === locale"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          class="check-icon"
        >
          <path d="M4 9L7.5 12.5L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'

defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const handleBlur = () => {
  // Delay to allow mousedown events on dropdown items to fire first
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

const selectLanguage = (locale) => {
  setLocale(locale)
  isDropdownOpen.value = false
}
</script>

<style scoped>
.language-switcher {
  position: relative;
}

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

.language-button {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  height: 40px;
  padding: 0 var(--space-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--transition-fast);
  font-family: inherit;
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

.language-button:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.language-button:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.language-button.is-collapsed {
  justify-content: center;
  padding: 0;
}

.globe-icon {
  flex-shrink: 0;
}

.language-label {
  flex: 1;
  text-align: left;
  font-weight: 500;
}

.chevron {
  color: var(--color-text-muted);
  transition: transform var(--transition-base);
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

/* Opens to the right of the sidebar, bottom edges aligned. The sidebar footer sits at
   the bottom of the viewport and is not an overflow container, so this is never clipped.
   Offset is space-4 (not space-2) to clear the footer padding and land just past the
   sidebar's right edge. */
.dropdown-menu {
  position: absolute;
  left: calc(100% + var(--space-4));
  bottom: 0;
  min-width: 160px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  z-index: var(--z-dropdown);
  overflow: hidden;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background-color var(--transition-fast);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  color: #334155;
}

.dropdown-item:hover {
  background: var(--color-bg);
}

.dropdown-item.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.language-name {
  flex: 1;
}

.check-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

/* Phone drawer: a 390px viewport has no room to the right of a 256px drawer, so open upward.
   Tablets keep the sideways placement of the desktop sidebar. */
@media (max-width: 767.98px) {
  .dropdown-menu {
    left: 0;
    bottom: calc(100% + var(--space-2));
    min-width: 100%;
  }
}
</style>
