'use client';

import { type PhaseId } from '@/types/processing';

interface PhaseStatus {
  id: PhaseId;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'waiting_feedback' | 'error';
  progress: number;
  canProvideHitl: boolean;
  description?: string;
}

interface PhaseProgressProps {
  phases: PhaseStatus[];
  currentPhase: PhaseId;
  onPhaseClick?: (phaseId: PhaseId) => void;
  className?: string;
}

export function PhaseProgress({ 
  phases, 
  currentPhase, 
  onPhaseClick, 
  className = "" 
}: PhaseProgressProps) {
  
  const getPhaseIcon = (phase: PhaseStatus) => {
    switch (phase.status) {
      case 'completed':
        return (
          <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        );
        
      case 'processing':
        return (
          <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
          </div>
        );
        
      case 'waiting_feedback':
        return (
          <div className="w-5 h-5 bg-yellow-500 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
          </div>
        );
        
      case 'error':
        return (
          <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
        );
        
      default: // pending
        return (
          <div className="w-5 h-5 bg-gray-300 rounded-full flex items-center justify-center">
            <div className="w-2 h-2 bg-gray-500 rounded-full" />
          </div>
        );
    }
  };

  const getStatusColor = (phase: PhaseStatus) => {
    switch (phase.status) {
      case 'completed':
        return 'text-green-600';
      case 'processing':
        return 'text-blue-600';
      case 'waiting_feedback':
        return 'text-yellow-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusText = (phase: PhaseStatus) => {
    switch (phase.status) {
      case 'completed':
        return 'Completed';
      case 'processing':
        return `Processing... ${phase.progress}%`;
      case 'waiting_feedback':
        return 'Awaiting feedback';
      case 'error':
        return 'Error';
      default:
        return 'Pending';
    }
  };

  return (
    <div className={`claude-phase-list ${className}`}>
      <div className="mb-4">
        <h3 className="font-semibold text-gray-900 mb-2">Generation Progress</h3>
        <p className="text-sm text-gray-600">
          Phase {currentPhase} of {phases.length}
        </p>
      </div>
      
      <div className="space-y-3">
        {phases.map((phase, index) => (
          <div
            key={phase.id}
            className={`claude-phase-item ${
              phase.status === 'processing' ? 'active' : ''
            } ${
              phase.status === 'completed' ? 'completed' : ''
            } ${
              phase.status === 'error' ? 'error' : ''
            } ${
              onPhaseClick ? 'cursor-pointer' : ''
            }`}
            onClick={() => onPhaseClick?.(phase.id)}
          >
            <div className="claude-phase-icon">
              {getPhaseIcon(phase)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="claude-phase-title truncate">
                {phase.name}
              </div>
              <div className={`claude-phase-status ${getStatusColor(phase)}`}>
                {getStatusText(phase)}
              </div>
              
              {/* Progress bar for processing phases */}
              {phase.status === 'processing' && phase.progress > 0 && (
                <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                  <div 
                    className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                    style={{ width: `${phase.progress}%` }}
                  />
                </div>
              )}
            </div>

            {/* Feedback indicator */}
            {phase.canProvideHitl && (
              <div className="ml-2 text-yellow-500">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Overall progress */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm text-gray-600">
            {Math.round((phases.filter(p => p.status === 'completed').length / phases.length) * 100)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-500"
            style={{ 
              width: `${(phases.filter(p => p.status === 'completed').length / phases.length) * 100}%` 
            }}
          />
        </div>
      </div>
    </div>
  );
}