<template>
	<div class="speed-control" role="group" aria-label="Target speed control">
		<button class="speed-btn" :disabled="disabled" @click="adjustTarget(-3)">
			<span class="label">-3</span>
		</button>
		<button class="speed-btn" :disabled="disabled" @click="adjustTarget(-1)">
			<span class="label">-1</span>
		</button>

		<div class="target-pill">
			<span class="target-value">{{ targetSpeed }}</span>
			<span class="target-unit">km/h</span>
		</div>

		<button class="speed-btn" :disabled="disabled" @click="adjustTarget(1)">
			<span class="label">+1</span>
		</button>
		<button class="speed-btn" :disabled="disabled" @click="adjustTarget(3)">
			<span class="label">+3</span>
		</button>
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
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 22px;
}

.speed-btn {
	position: relative;
	width: 70px;
	height: 58px;
	border: none;
	border-radius: 10px;
	cursor: pointer;
	font-family: inherit;
	font-weight: 700;
	letter-spacing: 0.5px;
	color: #dde4e8;
	background: linear-gradient(145deg, #7a7f7a, #565e5b);
	box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
	transition: filter 0.15s ease, transform 0.15s ease;
}

.speed-btn:not(:disabled):hover {
	filter: brightness(1.12);
	transform: translateY(-2px);
}

.speed-btn:not(:disabled):active {
	filter: brightness(0.95);
	transform: translateY(0);
}

.speed-btn:disabled {
	opacity: 0.4;
	cursor: not-allowed;
	transform: none;
	filter: none;
}

.speed-btn .label {
	font-size: 0.85rem;
}

.target-pill {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	width: 130px;
	height: 58px;
	border-radius: 12px;
	background: linear-gradient(145deg, #33404d, #202a33);
	color: #eefbe4;
	box-shadow:
		0 4px 14px rgba(0, 0, 0, 0.35),
		inset 0 1px 1px rgba(255, 255, 255, 0.08);
}

.target-value {
	font-size: 1.15rem;
	font-weight: 700;
	line-height: 1.1;
}

.target-unit {
	font-size: 0.62rem;
	font-weight: 600;
	letter-spacing: 0.5px;
	opacity: 0.75;
	text-transform: uppercase;
}

@media (max-width: 700px) {
	.speed-control {
		gap: 14px;
	}

	.speed-btn {
		width: 54px;
		height: 46px;
	}

	.speed-btn .label {
		font-size: 0.7rem;
	}

	.target-pill {
		width: 106px;
		height: 46px;
	}

	.target-value {
		font-size: 0.95rem;
	}

	.target-unit {
		font-size: 0.56rem;
	}
}

@media (max-height: 700px) {
	.speed-control {
		gap: 10px;
	}

	.speed-btn {
		width: 46px;
		height: 38px;
	}

	.speed-btn .label {
		font-size: 0.6rem;
	}

	.target-pill {
		width: 92px;
		height: 38px;
	}

	.target-value {
		font-size: 0.82rem;
	}

	.target-unit {
		font-size: 0.5rem;
	}
}
</style>
