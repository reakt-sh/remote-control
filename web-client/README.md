# remote-control

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Lints and fixes files
```
npm run lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).


# 🚀 Vue.js Coding Conventions

## 📁 Files & Directories
```bash
src/
├── components/    # PascalCase (e.g., `UserCard.vue`)
├── composables/   # `usePascalCase` (e.g., `useFetchData.js`)
├── views/         # PascalCase (e.g., `HomeView.vue`)
└── stores/        # camelCase (e.g., `userStore.js`)
```

## 🧩 Components
```vue
<!-- UserProfile.vue -->
<script>
export default {
  name: 'UserProfile',  // PascalCase
  props: { userId: Number },  // camelCase
  emits: ['update-user']  // kebab-case
}
</script>

<template>
  <div :user-id="123" @update-user="handleUpdate">  <!-- kebab-case -->
    {{ userName }}  <!-- camelCase -->
  </div>
</template>
```

## 📜 Script Conventions
- **Data/Refs:** `camelCase` (`userData`)
- **Methods:** `camelCase` (`fetchUser()`)
- **Computed:** `camelCase` (`formattedDate`)

## 🛠 State (Pinia)
```js
// stores/userStore.js
export const useUserStore = defineStore('user', {
  state: () => ({ user: null }),  // camelCase
  actions: { fetchUser() {} },    // camelCase
  getters: { getActiveUser: (state) => state.user }  // `get` prefix
})
```

## 🛣 Router
```js
const routes = [
  {
    path: '/user/:id',
    name: 'user-profile',  // kebab-case
    component: () => import('@/views/UserView.vue')  // PascalCase
  }
]
```

## 🎨 CSS (Scoped/BEM)
```vue
<style scoped>
.user-card { /* Block */ }
.user-card__title { /* Element */ }
.user-card--active { /* Modifier */ }
</style>
```

## ✅ Summary Table
| **Type**       | **Convention**   | **Example**          |
|----------------|------------------|----------------------|
| Components     | PascalCase       | `UserCard.vue`       |
| Props (Script) | camelCase        | `userId`             |
| Props (Template) | kebab-case     | `:user-id="123"`     |
| Events         | kebab-case       | `@update-user`       |
| Methods        | camelCase        | `fetchData()`        |
| Stores         | camelCase        | `userStore.js`       |

---
*Enforce with ESLint: `plugin:vue/vue3-recommended`*


