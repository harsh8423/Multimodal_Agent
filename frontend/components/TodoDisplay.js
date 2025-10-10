import React, { useState, useEffect } from 'react';
import { CheckCircleIcon, ClockIcon, PlayIcon, XCircleIcon } from '@heroicons/react/24/outline';

const TodoDisplay = ({ todoData, onTodoUpdate }) => {
  const [expandedTasks, setExpandedTasks] = useState(new Set());
  const [isExpanded, setIsExpanded] = useState(false);

  if (!todoData || !todoData.tasks) {
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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'done':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'in-progress':
        return <PlayIcon className="w-5 h-5 text-blue-500" />;
      case 'pending':
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
      default:
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'done':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'in-progress':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'pending':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-red-100 text-red-800 border-red-200';
    }
  };

  const completedTasks = todoData.tasks.filter(task => task.status === 'done').length;
  const totalTasks = todoData.tasks.length;
  const progressPercentage = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-4 mb-4">
      {/* Todo Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-semibold">📋</span>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{todoData.title}</h3>
            <p className="text-sm text-gray-500">
              Created by {todoData.created_by} • {new Date(todoData.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          {isExpanded ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </button>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span>{completedTasks}/{totalTasks} tasks completed</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Tasks List */}
      {isExpanded && (
        <div className="space-y-3">
          {todoData.tasks
            .sort((a, b) => (a.step_num || a.step) - (b.step_num || b.step))
            .map((task) => (
              <div
                key={task.step_num || task.step}
                className={`border rounded-lg p-3 transition-all duration-200 ${
                  task.status === 'done' 
                    ? 'bg-green-50 border-green-200' 
                    : task.status === 'in-progress'
                    ? 'bg-blue-50 border-blue-200'
                    : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-0.5">
                    {getStatusIcon(task.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900">
                        Step {task.step_num || task.step}: {task.title || task.description}
                      </h4>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(
                          task.status
                        )}`}
                      >
                        {task.status}
                      </span>
                    </div>
                    {task.description && (
                      <div className="mt-2">
                        <p className="text-sm text-gray-600">{task.description}</p>
                      </div>
                    )}
                    {task.updated_at && (
                      <p className="text-xs text-gray-400 mt-1">
                        Updated: {new Date(task.updated_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
        </div>
      )}

      {/* Todo Footer */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>
            Last updated: {new Date(todoData.updated_at).toLocaleString()}
          </span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            todoData.status === 'completed' 
              ? 'bg-green-100 text-green-800' 
              : todoData.status === 'active'
              ? 'bg-blue-100 text-blue-800'
              : 'bg-gray-100 text-gray-800'
          }`}>
            {todoData.status}
          </span>
        </div>
      </div>
    </div>
  );
};

export default TodoDisplay;