import { useEffect, useState } from 'react'

export default function Loading({ 
  message = "Analyzing...", 
  steps = null, 
  durations = null 
}) {
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    if (!steps || steps.length === 0) return;
    
    let step = 0
    const stepDurations = durations || Array(steps.length).fill(800);
    
    function advance() {
      step += 1
      if (step < steps.length) {
        setCurrentStep(step)
        setTimeout(advance, stepDurations[step] || 800)
      }
    }
    const timer = setTimeout(advance, stepDurations[0] || 800)
    return () => clearTimeout(timer)
  }, [steps, durations])

  return (
    <div className="loading-wrapper" role="status" aria-live="polite">
      <div className="loading-spinner" aria-hidden="true" />
      <div className="loading-title">{message}</div>
      {steps && steps.length > 0 && (
        <div className="loading-steps">
          {steps.map((step, idx) => {
            const isDone   = idx < currentStep
            const isActive = idx === currentStep
            return (
              <div
                key={step.id || idx}
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
      )}
    </div>
  )
}
