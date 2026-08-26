import { useEffect, useState } from 'react'

const STEPS = [
  { id: 'preprocessing', label: 'Preprocessing image' },
  { id: 'entropy',       label: 'Entropy analysis' },
  { id: 'ela',           label: 'ELA analysis' },
  { id: 'noise',         label: 'Noise analysis' },
  { id: 'texture',       label: 'Texture analysis' },
  { id: 'result',        label: 'Preparing result' },
]

const STEP_DURATIONS = [600, 900, 900, 700, 700, 400]

export default function Loading() {
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    let step = 0
    function advance() {
      step += 1
      if (step < STEPS.length) {
        setCurrentStep(step)
        setTimeout(advance, STEP_DURATIONS[step])
      }
    }
    const timer = setTimeout(advance, STEP_DURATIONS[0])
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="loading-wrapper" role="status" aria-live="polite">
      <div className="loading-spinner" aria-hidden="true" />
      <div className="loading-title">Analyzing image…</div>
      <div className="loading-steps">
        {STEPS.map((step, idx) => {
          const isDone   = idx < currentStep
          const isActive = idx === currentStep
          return (
            <div
              key={step.id}
              className={`loading-step${isDone ? ' done' : isActive ? ' active' : ''}`}
            >
              <div className={`step-icon${isDone ? ' done' : isActive ? ' active' : ''}`}>
                {isDone && <span style={{ fontSize: '0.6rem', color: '#fff' }}>✓</span>}
              </div>
              {step.label}
            </div>
          )
        })}
      </div>
    </div>
  )
}
