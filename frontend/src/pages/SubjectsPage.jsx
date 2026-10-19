import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/Modal';
import { DEFAULT_COLOR_SWATCHES } from '../config';
import { 
  Plus, 
  BookOpen, 
  Edit2, 
  Trash2, 
  AlertTriangle,
  Check
} from 'lucide-react';

const HEX_REGEX = /^#(?:[0-9a-fA-F]{3}){1,2}$/;

export default function SubjectsPage() {
  const { apiFetch } = useAuth();
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  // Add / Edit Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
  const [name, setName] = useState('');
  const [color, setColor] = useState(DEFAULT_COLOR_SWATCHES[0]);
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Delete Confirmation Modal state
  const [deleteConfirmSubject, setDeleteConfirmSubject] = useState(null);
  const [deleteTaskCount, setDeleteTaskCount] = useState(0);
  const [deleting, setDeleting] = useState(false);

  const fetchSubjects = async () => {
    try {
      const data = await apiFetch('/subjects');
      setSubjects(data);
    } catch (err) {
      console.error('Failed to fetch subjects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  const openAddModal = () => {
    setEditingSubject(null);
    setName('');
    setColor(DEFAULT_COLOR_SWATCHES[0]);
    setDescription('');
    setFormError('');
    setIsModalOpen(true);
  };

  const openEditModal = (subject) => {
    setEditingSubject(subject);
    setName(subject.name);
    setColor(subject.color);
    setDescription(subject.description || '');
    setFormError('');
    setIsModalOpen(true);
  };

  const handleSaveSubject = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!name.trim()) {
      setFormError('Subject name is required.');
      return;
    }

    if (!HEX_REGEX.test(color)) {
      setFormError('Please enter a valid Hex color code (e.g., #54552d).');
      return;
    }

    setSubmitting(true);
    try {
      if (editingSubject) {
        await apiFetch(`/subjects/${editingSubject.id}`, {
          method: 'PUT',
          body: JSON.stringify({
            name: name.trim(),
            color: color.trim(),
            description: description.trim()
          })
        });
      } else {
        await apiFetch('/subjects', {
          method: 'POST',
          body: JSON.stringify({
            name: name.trim(),
            color: color.trim(),
            description: description.trim()
          })
        });
      }
      setIsModalOpen(false);
      fetchSubjects();
    } catch (err) {
      setFormError(err.message || 'Failed to save subject');
    } finally {
      setSubmitting(false);
    }
  };

  const promptDeleteSubject = async (subject) => {
    try {
      const data = await apiFetch(`/subjects/${subject.id}/task-count`);
      setDeleteTaskCount(data.task_count);
      setDeleteConfirmSubject(subject);
    } catch (err) {
      console.error('Failed to get task count for subject:', err);
    }
  };

  const confirmDeleteSubject = async () => {
    if (!deleteConfirmSubject) return;
    setDeleting(true);
    try {
      await apiFetch(`/subjects/${deleteConfirmSubject.id}`, { method: 'DELETE' });
      setDeleteConfirmSubject(null);
      fetchSubjects();
    } catch (err) {
      alert(err.message || 'Failed to delete subject');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="subjects-page">
      <div className="page-header">
        <div className="page-title-group">
          <h2>Subjects</h2>
          <p>Organize your academic curriculum, assign custom accent colors, and track tasks.</p>
        </div>

        <button
          id="add-subject-btn"
          type="button"
          className="btn btn-primary"
          onClick={openAddModal}
        >
          <Plus size={16} />
          <span>Add Subject</span>
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          Loading subjects...
        </div>
      ) : subjects.length === 0 ? (
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          padding: '48px 20px',
          textAlign: 'center'
        }}>
          <BookOpen size={48} style={{ color: 'var(--text-muted)', marginBottom: '12px', opacity: 0.5 }} />
          <h3 style={{ fontSize: '18px', marginBottom: '6px' }}>No Subjects Added Yet</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', maxWidth: '400px', margin: '0 auto 20px auto' }}>
            Create your course subjects or revision topics to start assigning and scheduling study tasks.
          </p>
          <button type="button" className="btn btn-primary" onClick={openAddModal}>
            <Plus size={16} />
            <span>Create Your First Subject</span>
          </button>
        </div>
      ) : (
        <div className="subjects-grid">
          {subjects.map((subject) => (
            <div key={subject.id} className="subject-card" id={`subject-card-${subject.id}`}>
              <div className="subject-color-bar" style={{ backgroundColor: subject.color }}></div>
              <div>
                <div className="subject-header">
                  <div className="subject-name-group">
                    <span 
                      className="color-dot" 
                      style={{ backgroundColor: subject.color, width: '12px', height: '12px' }}
                    ></span>
                    <h3>{subject.name}</h3>
                  </div>

                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary btn-icon"
                      title="Edit Subject"
                      onClick={() => openEditModal(subject)}
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      type="button"
                      className="btn btn-danger btn-icon"
                      title="Delete Subject"
                      onClick={() => promptDeleteSubject(subject)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>

                {subject.description && (
                  <p className="subject-desc">{subject.description}</p>
                )}
              </div>

              <div className="subject-footer">
                <span className="subject-task-count">
                  {subject.task_count} {subject.task_count === 1 ? 'Task' : 'Tasks'}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                  {subject.color}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Subject Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingSubject ? 'Edit Subject' : 'Add Subject'}
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
              id="save-subject-btn"
              type="submit"
              form="subject-form"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Saving...' : (editingSubject ? 'Update Subject' : 'Create Subject')}
            </button>
          </>
        }
      >
        <form id="subject-form" onSubmit={handleSaveSubject}>
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

          <div className="form-group">
            <label className="form-label" htmlFor="subject-name">Subject Name *</label>
            <input
              id="subject-name"
              type="text"
              className="form-input"
              placeholder="e.g. Software Project Management"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Accent Color *</label>
            <div className="swatches-row">
              {DEFAULT_COLOR_SWATCHES.map((swatch) => (
                <button
                  key={swatch}
                  type="button"
                  className={`color-swatch-btn ${color.toLowerCase() === swatch.toLowerCase() ? 'selected' : ''}`}
                  style={{ backgroundColor: swatch }}
                  onClick={() => setColor(swatch)}
                  title={swatch}
                />
              ))}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '6px' }}>
              <input
                id="subject-color-hex"
                type="text"
                className="form-input"
                placeholder="#54552d"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                maxLength={7}
                style={{ fontFamily: 'monospace' }}
              />
              <div 
                style={{ 
                  width: '38px', 
                  height: '38px', 
                  borderRadius: 'var(--radius-md)', 
                  backgroundColor: HEX_REGEX.test(color) ? color : 'transparent',
                  border: '1px solid var(--border-color)',
                  flexShrink: 0
                }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="subject-desc">Description (Optional)</label>
            <textarea
              id="subject-desc"
              className="form-textarea"
              placeholder="Brief overview or syllabus note..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <Modal
        isOpen={Boolean(deleteConfirmSubject)}
        onClose={() => setDeleteConfirmSubject(null)}
        title="Confirm Subject Deletion"
        footer={
          <>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setDeleteConfirmSubject(null)}
            >
              Cancel
            </button>
            <button
              id="confirm-delete-subject-btn"
              type="button"
              className="btn btn-danger"
              onClick={confirmDeleteSubject}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete Subject & Tasks'}
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '50%',
            backgroundColor: 'var(--danger-bg)',
            color: 'var(--danger-text)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            <AlertTriangle size={22} />
          </div>

          <div>
            <h4 style={{ fontSize: '16px', marginBottom: '6px' }}>
              Delete "{deleteConfirmSubject?.name}"?
            </h4>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
              Are you sure you want to delete this subject?
            </p>
            {deleteTaskCount > 0 ? (
              <p style={{
                marginTop: '10px',
                fontSize: '13px',
                fontWeight: 600,
                color: 'var(--danger-text)',
                backgroundColor: 'var(--danger-bg)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)'
              }}>
                Warning: Deleting this subject will also delete {deleteTaskCount} associated task(s) and any planned calendar sessions.
              </p>
            ) : (
              <p style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>
                This subject currently has 0 tasks.
              </p>
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
}
