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
	gap: clamp(10px, 4cqh, 22px);
}

/* Sized off the control panel's own height (cqh) so buttons scale up to
   fill leftover space on tall/short screens alike, instead of relying on
   fixed viewport breakpoints. */
.speed-btn {
	position: relative;
	width: clamp(46px, 14cqh, 108px);
	height: clamp(38px, 12cqh, 90px);
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
	font-size: clamp(0.6rem, 3cqh, 0.85rem);
}

.target-pill {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	width: clamp(92px, 28cqh, 210px);
	height: clamp(38px, 12cqh, 90px);
	border-radius: 12px;
	background: linear-gradient(145deg, #33404d, #202a33);
	color: #eefbe4;
	box-shadow:
		0 4px 14px rgba(0, 0, 0, 0.35),
		inset 0 1px 1px rgba(255, 255, 255, 0.08);
}

.target-value {
	font-size: clamp(0.82rem, 3.6cqh, 1.15rem);
	font-weight: 700;
	line-height: 1.1;
}

.target-unit {
	font-size: clamp(0.5rem, 1.6cqh, 0.65rem);
	font-weight: 600;
	letter-spacing: 0.5px;
	opacity: 0.75;
	text-transform: uppercase;
}

/* Landscape has more headroom (the control panel gets a taller share of
   the viewport), so let the buttons scale up further before hitting their
   caps instead of staying capped at the portrait-friendly sizes. */
@media (orientation: landscape) {
	.speed-control {
		gap: clamp(12px, 5cqh, 28px);
	}

	.speed-btn {
		width: clamp(54px, 17cqh, 130px);
		height: clamp(46px, 15cqh, 115px);
	}

	.speed-btn .label {
		font-size: clamp(0.68rem, 3.6cqh, 1rem);
	}

	.target-pill {
		width: clamp(108px, 33cqh, 250px);
		height: clamp(46px, 15cqh, 115px);
	}

	.target-value {
		font-size: clamp(0.95rem, 4.2cqh, 1.35rem);
	}

	.target-unit {
		font-size: clamp(0.56rem, 1.9cqh, 0.75rem);
	}
}
</style>
