/**
 * Todo API Service
 * Handles all todo-related API calls
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

class TodoAPI {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async getChatTodos(chatId, token, status = null) {
    try {
      const url = new URL(`${this.baseURL}/todos/chat/${chatId}`);
      if (status) {
        url.searchParams.append('status', status);
      }
      url.searchParams.append('token', token);

      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching chat todos:', error);
      throw error;
    }
  }

  async getTodo(todoId, token) {
    try {
      const url = new URL(`${this.baseURL}/todos/${todoId}`);
      url.searchParams.append('token', token);

      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching todo:', error);
      throw error;
    }
  }

  async createTodo(token, chatId, title, tasks, agentName = 'social_media_manager') {
    try {
      const response = await fetch(`${this.baseURL}/todos/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token,
          title,
          tasks: tasks.map(task => ({
            ...task,
            chat_id: chatId
          }))
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error creating todo:', error);
      throw error;
    }
  }

  async updateTodoTask(token, todoId, stepNum, status, title = null, description = null) {
    try {
      const response = await fetch(`${this.baseURL}/todos/${todoId}/task/${stepNum}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token,
          todo_id: todoId,
          step_num: stepNum,
          status,
          title,
          description
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error updating todo task:', error);
      throw error;
    }
  }

  async getNextTodoTask(todoId, token) {
    try {
      const url = new URL(`${this.baseURL}/todos/${todoId}/next-task`);
      url.searchParams.append('token', token);

      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching next todo task:', error);
      throw error;
    }
  }
}

export const todoAPI = new TodoAPI();
export default todoAPI;