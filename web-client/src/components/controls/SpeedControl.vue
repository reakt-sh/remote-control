<template>
	<div class="speed-control" role="group" aria-label="Target speed control">
		<button class="speed-btn" :disabled="disabled" @click="adjustTarget(-3)">-3</button>
		<button class="speed-btn" :disabled="disabled" @click="adjustTarget(-1)">-1</button>

		<div class="target-pill">{{ targetSpeed }} km/h</div>

		<button class="speed-btn" :disabled="disabled" @click="adjustTarget(1)">+1</button>
		<button class="speed-btn" :disabled="disabled" @click="adjustTarget(3)">+3</button>
	</div>
</template>

<script setup>
const props = defineProps({
	targetSpeed: {
		type: Number,
		default: 0
	},
	maxSpeed: {
		type: Number,
		default: 13
	},
	disabled: {
		type: Boolean,
		default: false
	}
})

const emit = defineEmits(['update:targetSpeed', 'change:targetSpeed'])

function adjustTarget(delta) {
	const next = Math.max(0, Math.min(props.maxSpeed, props.targetSpeed + delta))
	emit('update:targetSpeed', next)
	emit('change:targetSpeed', next)
}
</script>

<style scoped>
.speed-control {
	width: 100%;
	max-width: 420px;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	flex-wrap: nowrap;
}

.speed-btn {
	min-width: 52px;
	height: 36px;
	border: 1px solid #d6dbdf;
	border-radius: 8px;
	background: #f8f9fa;
	color: #2c3e50;
	font-weight: 600;
	cursor: pointer;
	transition: all 0.2s;
}

.speed-btn:hover:not(:disabled) {
	background: #e7edf2;
	border-color: #c8d1d9;
}

.speed-btn:active:not(:disabled) {
	transform: scale(0.98);
}

.speed-btn:disabled {
	opacity: 0.5;
	cursor: not-allowed;
}

.target-pill {
	min-width: 170px;
	text-align: center;
	padding: 8px 12px;
	border-radius: 999px;
	background: #2c3e50;
	color: #fff;
	font-size: 0.9rem;
	font-weight: 600;
}

@media (max-width: 599px) {
	.speed-control {
		gap: 6px;
	}

	.speed-btn {
		min-width: 46px;
		height: 34px;
	}

	.target-pill {
		min-width: 150px;
		font-size: 0.82rem;
		padding: 7px 10px;
	}
}
</style>
