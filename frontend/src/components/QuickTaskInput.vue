<template>
  <div class="quick-task-input">
    <input
      v-model="inputValue"
      type="text"
      placeholder="快速添加任务..."
      @keydown.enter="handleEnter"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const inputValue = ref('')

const emit = defineEmits(['taskCreate'])

const handleEnter = () => {
  if (inputValue.value.trim()) {
    emit('taskCreate', inputValue.value)
    inputValue.value = ''
  }
}
</script>

<style scoped>
.quick-task-input {
  padding: 12px;
}

input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}
</style>
