import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/Modal';
import { 
  Plus, 
  Search, 
  Filter, 
  Calendar, 
  Clock, 
  Check, 
  Edit2, 
  Trash2, 
  AlertCircle,
  AlertTriangle,
  BookOpen
} from 'lucide-react';

export default function TasksPage({ onNavigateToSubjects }) {
  const { apiFetch } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  // Search & Filter state
  const [search, setSearch] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedPriority, setSelectedPriority] = useState('all');
  const [sortBy, setSortBy] = useState('due_date_asc');

  // Add / Edit Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [title, setTitle] = useState('');
  const [subjectId, setSubjectId] = useState('');
  const [taskType, setTaskType] = useState('Assignment');
  const [dueDate, setDueDate] = useState('');
  const [priority, setPriority] = useState('Medium');
  const [status, setStatus] = useState('Pending');
  const [durationMins, setDurationMins] = useState(45);
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Delete modal state
  const [deleteTaskObj, setDeleteTaskObj] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Fetch subjects
  const fetchSubjects = async () => {
    try {
      const data = await apiFetch('/subjects');
      setSubjects(data);
    } catch (err) {
      console.error('Failed to load subjects:', err);
    }
  };

  // Fetch tasks with filters
  const fetchTasks = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (selectedSubject !== 'all') params.append('subject_id', selectedSubject);
      if (selectedStatus !== 'all') params.append('status', selectedStatus);
      if (selectedPriority !== 'all') params.append('priority', selectedPriority);
      params.append('sort_by', sortBy);

      const data = await apiFetch(`/tasks?${params.toString()}`);
      setTasks(data);
    } catch (err) {
      console.error('Failed to fetch tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [search, selectedSubject, selectedStatus, selectedPriority, sortBy]);

  const openAddModal = () => {
    setEditingTask(null);
    setTitle('');
    setSubjectId(subjects.length > 0 ? subjects[0].id : '');
    setTaskType('Assignment');

    // Default due date: tomorrow at 18:00 in YYYY-MM-DDTHH:MM
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(18, 0, 0, 0);
    const yyyy = tomorrow.getFullYear();
    const mm = String(tomorrow.getMonth() + 1).padStart(2, '0');
    const dd = String(tomorrow.getDate()).padStart(2, '0');
    const hh = String(tomorrow.getHours()).padStart(2, '0');
    const min = String(tomorrow.getMinutes()).padStart(2, '0');
    setDueDate(`${yyyy}-${mm}-${dd}T${hh}:${min}`);

    setPriority('Medium');
    setStatus('Pending');
    setDurationMins(45);
    setDescription('');
    setFormError('');
    setIsModalOpen(true);
  };

  const openEditModal = (task) => {
    setEditingTask(task);
    setTitle(task.title);
    setSubjectId(task.subject_id);
    setTaskType(task.task_type);
    setDueDate(task.due_date ? task.due_date.slice(0, 16) : '');
    setPriority(task.priority);
    setStatus(task.status);
    setDurationMins(task.duration_mins);
    setDescription(task.description || '');
    setFormError('');
    setIsModalOpen(true);
  };

  const handleSaveTask = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!title.trim()) {
      setFormError('Task title is required.');
      return;
    }
    if (!subjectId) {
      setFormError('Please select a subject.');
      return;
    }
    if (!dueDate) {
      setFormError('Due date and time is required.');
      return;
    }
    if (!durationMins || Number(durationMins) <= 0) {
      setFormError('Duration must be greater than 0 minutes.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        title: title.trim(),
        subject_id: Number(subjectId),
        task_type: taskType,
        due_date: dueDate,
        priority,
        status,
        duration_mins: Number(durationMins),
        description: description.trim()
      };

      if (editingTask) {
        await apiFetch(`/tasks/${editingTask.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload)
        });
      } else {
        await apiFetch('/tasks', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
      }
      setIsModalOpen(false);
      fetchTasks();
    } catch (err) {
      setFormError(err.message || 'Failed to save task');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleTask = async (taskId) => {
    try {
      await apiFetch(`/tasks/${taskId}/toggle`, { method: 'PATCH' });
      fetchTasks();
    } catch (err) {
      console.error('Failed to toggle task:', err);
    }
  };

  const confirmDeleteTask = async () => {
    if (!deleteTaskObj) return;
    setDeleting(true);
    try {
      await apiFetch(`/tasks/${deleteTaskObj.id}`, { method: 'DELETE' });
      setDeleteTaskObj(null);
      fetchTasks();
    } catch (err) {
      alert(err.message || 'Failed to delete task');
    } finally {
      setDeleting(false);
    }
  };

  // Format date nicely: "Oct 20, 2026 at 18:00"
  const formatDateTime = (isoStr) => {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="tasks-page">
      <div className="page-header">
        <div className="page-title-group">
          <h2>Tasks</h2>
          <p>Manage, prioritize, and track your assignments and revision milestones.</p>
        </div>

        <button
          id="add-task-btn"
          type="button"
          className="btn btn-primary"
          onClick={openAddModal}
        >
          <Plus size={16} />
          <span>Add Task</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div className="filters-bar">
        <div className="search-box">
          <Search size={16} className="search-icon" />
          <input
            id="task-search-input"
            type="text"
            className="form-input"
            placeholder="Search by title or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Subject filter */}
        <div className="filter-item">
          <select
            id="filter-subject"
            className="form-select"
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
          >
            <option value="all">All Subjects</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        {/* Status filter */}
        <div className="filter-item">
          <select
            id="filter-status"
            className="form-select"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="Complete">Complete</option>
          </select>
        </div>

        {/* Priority filter */}
        <div className="filter-item">
          <select
            id="filter-priority"
            className="form-select"
            value={selectedPriority}
            onChange={(e) => setSelectedPriority(e.target.value)}
          >
            <option value="all">All Priorities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>

        {/* Sort by */}
        <div className="filter-item" style={{ minWidth: '190px' }}>
          <select
            id="sort-tasks-by"
            className="form-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="due_date_asc">Due date (earliest first)</option>
            <option value="due_date_desc">Due date (latest first)</option>
            <option value="priority_desc">Priority (high to low)</option>
            <option value="duration_desc">Duration (longest first)</option>
            <option value="created_at_desc">Recently created</option>
          </select>
        </div>
      </div>

      {/* Task List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          Loading tasks...
        </div>
      ) : tasks.length === 0 ? (
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          padding: '48px 20px',
          textAlign: 'center'
        }}>
          <Check size={48} style={{ color: 'var(--text-muted)', marginBottom: '12px', opacity: 0.5 }} />
          <h3 style={{ fontSize: '18px', marginBottom: '6px' }}>No Tasks Found</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', maxWidth: '400px', margin: '0 auto 20px auto' }}>
            {subjects.length === 0 
              ? 'You need to create at least one subject before adding tasks.' 
              : 'Add a new task or adjust your search filters to view your study queue.'}
          </p>
          {subjects.length === 0 ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={onNavigateToSubjects}
            >
              <BookOpen size={16} />
              <span>Go to Subjects Page</span>
            </button>
          ) : (
            <button type="button" className="btn btn-primary" onClick={openAddModal}>
              <Plus size={16} />
              <span>Add Your First Task</span>
            </button>
          )}
        </div>
      ) : (
        <div className="tasks-list">
          {tasks.map((task) => {
            const isComplete = task.status === 'Complete';
            const isOverdue = task.is_overdue;

            return (
              <div
                key={task.id}
                id={`task-item-${task.id}`}
                className={`task-item ${isComplete ? 'is-complete' : ''} ${isOverdue ? 'is-overdue' : ''}`}
              >
                <div className="task-main">
                  {/* Quick toggle completion checkbox */}
                  <button
                    type="button"
                    className={`task-checkbox ${isComplete ? 'checked' : ''}`}
                    onClick={() => handleToggleTask(task.id)}
                    title={isComplete ? 'Mark as Pending' : 'Mark as Complete'}
                    aria-label={`Toggle status for ${task.title}`}
                  >
                    <Check size={14} />
                  </button>

                  <div className="task-details">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="task-title">{task.title}</span>
                      {isOverdue && (
                        <span className="badge-risk">
                          <AlertTriangle size={11} /> Overdue
                        </span>
                      )}
                    </div>

                    <div className="task-meta">
                      <div className="subject-badge">
                        <span 
                          className="color-dot" 
                          style={{ backgroundColor: task.subject_color }}
                        />
                        <span>{task.subject_name}</span>
                      </div>

                      <span style={{ color: 'var(--border-strong)' }}>•</span>

                      <div className="task-meta-item">
                        <span style={{ 
                          fontSize: '11px', 
                          fontWeight: 600, 
                          color: 'var(--text-secondary)',
                          backgroundColor: 'var(--accent-soft)',
                          padding: '1px 6px',
                          borderRadius: '4px'
                        }}>
                          {task.task_type}
                        </span>
                      </div>

                      <span style={{ color: 'var(--border-strong)' }}>•</span>

                      <div className="task-meta-item">
                        <Calendar size={13} />
                        <span>Due {formatDateTime(task.due_date)}</span>
                      </div>

                      <span style={{ color: 'var(--border-strong)' }}>•</span>

                      <div className="task-meta-item">
                        <Clock size={13} />
                        <span>{task.duration_mins} mins</span>
                      </div>

                      <span style={{ color: 'var(--border-strong)' }}>•</span>

                      <span className={`priority-badge priority-${task.priority.toLowerCase()}`}>
                        {task.priority}
                      </span>
                    </div>

                    {task.description && (
                      <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                        {task.description}
                      </p>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    type="button"
                    className="btn btn-secondary btn-icon"
                    title="Edit Task"
                    onClick={() => openEditModal(task)}
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    type="button"
                    className="btn btn-danger btn-icon"
                    title="Delete Task"
                    onClick={() => setDeleteTaskObj(task)}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add / Edit Task Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingTask ? 'Edit Task' : 'Add Task'}
        footer={
          <>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </button>
            <button
              id="save-task-btn"
              type="submit"
              form="task-form"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Saving...' : (editingTask ? 'Update Task' : 'Create Task')}
            </button>
          </>
        }
      >
        <form id="task-form" onSubmit={handleSaveTask}>
          {formError && (
            <div style={{
              backgroundColor: 'var(--danger-bg)',
              color: 'var(--danger-text)',
              border: '1px solid var(--danger-border)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              fontSize: '13px',
              marginBottom: '16px'
            }}>
              {formError}
            </div>
          )}

          {subjects.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <p style={{ color: 'var(--danger-text)', marginBottom: '12px' }}>
                You must create a subject first before adding tasks!
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  setIsModalOpen(false);
                  onNavigateToSubjects();
                }}
              >
                Go to Subjects to Add One
              </button>
            </div>
          ) : (
            <>
              <div className="form-group">
                <label className="form-label" htmlFor="task-title">Title *</label>
                <input
                  id="task-title"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Chapter 4 Practice Exercises"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  autoFocus
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div className="form-group">
                  <label className="form-label" htmlFor="task-subject">Subject *</label>
                  <select
                    id="task-subject"
                    className="form-select"
                    value={subjectId}
                    onChange={(e) => setSubjectId(e.target.value)}
                    required
                  >
                    {subjects.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="task-type">Task Type *</label>
                  <select
                    id="task-type"
                    className="form-select"
                    value={taskType}
                    onChange={(e) => setTaskType(e.target.value)}
                  >
                    <option value="Assignment">Assignment</option>
                    <option value="Revision">Revision</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div className="form-group">
                  <label className="form-label" htmlFor="task-due-date">Due Date & Time *</label>
                  <input
                    id="task-due-date"
                    type="datetime-local"
                    className="form-input"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="task-priority">Priority *</label>
                  <select
                    id="task-priority"
                    className="form-select"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                  >
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div className="form-group">
                  <label className="form-label" htmlFor="task-duration">Estimated Duration (mins) *</label>
                  <input
                    id="task-duration"
                    type="number"
                    className="form-input"
                    min="5"
                    step="5"
                    value={durationMins}
                    onChange={(e) => setDurationMins(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="task-status">Status</label>
                  <select
                    id="task-status"
                    className="form-select"
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                  >
                    <option value="Pending">Pending</option>
                    <option value="Complete">Complete</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="task-desc">Description (Optional)</label>
                <textarea
                  id="task-desc"
                  className="form-textarea"
                  placeholder="Key questions to answer, page numbers, or notes..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </>
          )}
        </form>
      </Modal>

      {/* Delete Task Confirmation */}
      <Modal
        isOpen={Boolean(deleteTaskObj)}
        onClose={() => setDeleteTaskObj(null)}
        title="Confirm Task Deletion"
        footer={
          <>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setDeleteTaskObj(null)}
            >
              Cancel
            </button>
            <button
              id="confirm-delete-task-btn"
              type="button"
              className="btn btn-danger"
              onClick={confirmDeleteTask}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete Task'}
            </button>
          </>
        }
      >
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Are you sure you want to delete task <strong>"{deleteTaskObj?.title}"</strong>? Any planned sessions associated with this task will also be removed.
        </p>
      </Modal>
    </div>
  );
}
