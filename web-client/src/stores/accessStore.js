import { defineStore } from 'pinia'
import { ref } from 'vue'

const ACCESS_CODE = 'rc2026' // Change this to your desired secret code

export const useAccessStore = defineStore('access', () => {
  const isGranted = ref(sessionStorage.getItem('rc_access_granted') === 'true')

  function grantAccess() {
    isGranted.value = true
    sessionStorage.setItem('rc_access_granted', 'true')
  }

  function checkCode(code) {
    return code === ACCESS_CODE
  }

  function revokeAccess() {
    isGranted.value = false
    sessionStorage.removeItem('rc_access_granted')
  }

  return { isGranted, grantAccess, checkCode, revokeAccess }
})