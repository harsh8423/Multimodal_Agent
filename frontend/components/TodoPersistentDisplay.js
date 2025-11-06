import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  Circle, 
  Play, 
  ChevronUp, 
  ChevronDown,
  Clock,
  XCircle,
  CheckCircle2
} from 'lucide-react';
import { cn } from '@/lib/utils';

const TodoPersistentDisplay = ({ 
  todoData, 
  onTodoUpdate,
  isExpanded = false,
  onToggleExpanded = () => {},
  className = "",
  hasNanoMessages = false
}) => {
  const [expandedTasks, setExpandedTasks] = useState(new Set());
  const [currentTodoData, setCurrentTodoData] = useState(todoData);

  // Update local state when todoData prop changes
  useEffect(() => {
    if (todoData) {
      setCurrentTodoData(todoData);
    }
  }, [todoData]);

  if (!currentTodoData || !currentTodoData.tasks) {
    return null;
  }

  const toggleTaskExpansion = (stepNum) => {
    const newExpanded = new Set(expandedTasks);
    if (newExpanded.has(stepNum)) {
      newExpanded.delete(stepNum);
    } else {
      newExpanded.add(stepNum);
    }
    setExpandedTasks(newExpanded);
  };

  const getStatusIcon = (status, isActive = false) => {
    if (isActive) {
      return <div className="w-3 h-3 rounded-full bg-blue-500 flex items-center justify-center">
        <Play className="w-2 h-2 text-white" />
      </div>;
    }
    
    switch (status) {
      case 'done':
      case 'completed':
        return <div className="w-3 h-3 rounded-full bg-green-500 flex items-center justify-center">
          <CheckCircle2 className="w-2 h-2 text-white" />
        </div>;
      case 'in-progress':
        return <div className="w-3 h-3 rounded-full bg-blue-500 flex items-center justify-center">
          <Play className="w-2 h-2 text-white" />
        </div>;
      case 'pending':
        return <Circle className="w-3 h-3 text-gray-400" />;
      default:
        return <XCircle className="w-3 h-3 text-red-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'done':
      case 'completed':
        return 'text-green-600';
      case 'in-progress':
        return 'text-blue-600';
      case 'pending':
        return 'text-gray-500';
      default:
        return 'text-red-600';
    }
  };

  const completedTasks = currentTodoData.tasks.filter(task => 
    task.status === 'done' || task.status === 'completed'
  ).length;
  const totalTasks = currentTodoData.tasks.length;
  const activeTask = currentTodoData.tasks.find(task => task.status === 'in-progress');
  const progressPercentage = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  // Determine if todo should be shown (not all completed and status is active)
  const shouldShow = currentTodoData.status === 'active' && completedTasks < totalTasks;

  if (!shouldShow) {
    return null;
  }

  return (
    <div className={cn("relative", className)}>
      {/* Todo Header Bar - Similar to nano message style */}
      <div className={cn(
        "flex items-center px-3 py-2 text-[11px] font-mono text-gray-600 bg-white/90 backdrop-blur-md border border-gray-200/80 border-b-0",
        hasNanoMessages ? "rounded-t-3xl" : "rounded-3xl"
      )}>
        <button
          type="button"
          className="mr-2 p-0.5 text-gray-500 hover:text-gray-700"
          onClick={onToggleExpanded}
          title={isExpanded ? 'Hide details' : 'Show details'}
        >
          {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
        </button>
        
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <span className="text-gray-800 font-semibold">
            {completedTasks} of {totalTasks} To-dos
          </span>
          {activeTask && (
            <span className="truncate text-gray-500">
              {activeTask.title}
            </span>
          )}
        </div>
        
        {/* Progress indicator */}
        <div className="flex items-center gap-1 ml-2">
          <div className="w-8 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Expanded Todo List */}
      {isExpanded && (
        <div className="absolute bottom-full mb-1 left-0 right-0 rounded-lg border border-gray-200 bg-white shadow-lg overflow-hidden">
          <div className="max-h-60 overflow-y-auto py-1">
            {/* Todo Title */}
            <div className="px-3 py-2 border-b border-gray-100">
              <h3 className="text-sm font-semibold text-gray-900">{currentTodoData.title}</h3>
            </div>
            
            {/* Tasks List */}
            {currentTodoData.tasks.map((task, index) => {
              const isActive = task.status === 'in-progress';
              const isExpanded = expandedTasks.has(task.step_num);
              
              return (
                <div key={task.step_num} className="px-3 py-1.5 text-[11px] font-mono">
                  <div className="flex items-center gap-2">
                    {/* Status Icon */}
                    <div className="flex-shrink-0">
                      {getStatusIcon(task.status, isActive)}
                    </div>
                    
                    {/* Task Content */}
                    <div className="min-w-0 flex-1">
                      <div className={cn(
                        "truncate",
                        getStatusColor(task.status),
                        isActive && "font-semibold"
                      )}>
                        {task.title}
                      </div>
                      
                      {/* Task Description (if expanded) */}
                      {isExpanded && task.description && (
                        <div className="mt-1 text-xs text-gray-500 leading-relaxed">
                          {task.description}
                        </div>
                      )}
                    </div>
                    
                    {/* Expand/Collapse Button */}
                    {task.description && (
                      <button
                        onClick={() => toggleTaskExpansion(task.step_num)}
                        className="flex-shrink-0 p-0.5 text-gray-400 hover:text-gray-600"
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-3 h-3" />
                        ) : (
                          <ChevronDown className="w-3 h-3" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default TodoPersistentDisplay;