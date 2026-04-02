import { NavLink } from 'react-router-dom';

import { processSteps } from '../../data/navigation';

export function ProcessStepper() {
  return (
    <div className="process-stepper">
      {processSteps.map((step) => (
        <NavLink key={step.path} to={step.path} className={({ isActive }) => (isActive ? 'process-tab active' : 'process-tab')}>
          <span className="process-tab-label">{step.label}</span>
        </NavLink>
      ))}
    </div>
  );
}
