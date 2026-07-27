<template>
	<div class="speed-control" role="group" aria-label="Target speed control">
		<button
			class="speed-btn"
			:disabled="disabled || targetSpeed + (-3) < 0"
			@click="adjustTarget(-3)">
			<span class="label">-3</span>
		</button>
		<button
			class="speed-btn"
			:disabled="disabled || targetSpeed + (-1) < 0"
			@click="adjustTarget(-1)">
			<span class="label">-1</span>
		</button>

		<div class="target-pill">
			<span class="target-value">{{ targetSpeed }}</span>
			<span class="target-unit">km/h</span>
		</div>

		<button
			class="speed-btn"
			:disabled="disabled || targetSpeed + 1 > maxSpeed"
			@click="adjustTarget(1)">
			<span class="label">+1</span>
		</button>
		<button
			class="speed-btn"
			:disabled="disabled || targetSpeed + 3 > maxSpeed"
			@click="adjustTarget(3)">
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
	font-size: clamp(0.75rem, 3.8cqh, 1.05rem);
}

.target-pill {
	position: relative;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	width: clamp(92px, 28cqh, 210px);
	height: clamp(38px, 12cqh, 90px);
	background: none;
	border-radius: 12px;
	border: none;
	box-shadow: none;
	user-select: none;
}

.target-value {
	font-size: clamp(1.35rem, 6cqh, 2rem);
	font-weight: 800;
	line-height: 1.1;
	letter-spacing: 2px;
	color: #2c3e50;
	text-shadow: none;
	margin-bottom: 2px;
}

.target-unit {
	font-size: clamp(0.6rem, 2cqh, 0.8rem);
	font-weight: 500;
	letter-spacing: 2px;
	opacity: 0.4;
	text-transform: uppercase;
}

/* Landscape has more headroom (the control panel gets a taller share of
   the viewport), so let the buttons scale up further before hitting their
   caps instead of staying capped at the portrait-friendly sizes. */
@media (orientation: landscape) {
	.speed-control {
		gap: clamp(14px, 6cqh, 32px);
	}

	.speed-btn {
		width: clamp(70px, 22cqh, 160px);
		height: clamp(60px, 19cqh, 140px);
	}

	.speed-btn .label {
		font-size: clamp(0.95rem, 5cqh, 1.35rem);
	}

	.target-pill {
		width: clamp(130px, 38cqh, 300px);
		height: clamp(60px, 19cqh, 140px);
	}

	.target-value {
		font-size: clamp(1.25rem, 5.8cqh, 1.8rem);
	}

	.target-unit {
		font-size: clamp(0.75rem, 2.8cqh, 1.05rem);
	}
}
</style>
