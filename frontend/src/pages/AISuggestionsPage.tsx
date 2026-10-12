import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  Brain,
  CheckCircle2,
  XCircle,
  Clock,
  Calendar,
  AlertCircle,
  Info,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Cpu
} from 'lucide-react';
import { Recommendation, ModelStatus } from '../types';
import { api } from '../services/api';
import { Modal } from '../components/common/Modal';

export const AISuggestionsPage: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [genLoading, setGenLoading] = useState<boolean>(false);
  const [horizon, setHorizon] = useState<number>(5);

  // Accept/Reject feedback modal
  const [activeRec, setActiveRec] = useState<Recommendation | null>(null);
  const [feedbackAction, setFeedbackAction] = useState<'accept' | 'reject'>('accept');
  const [feedbackNote, setFeedbackNote] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [recs, status] = await Promise.all([
        api.getRecommendations('Pending'),
        api.getAIStatus()
      ]);
      setRecommendations(recs);
      setModelStatus(status);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    try {
      setGenLoading(true);
      const recs = await api.generateRecommendations({
        horizon_days: horizon,
        candidate_slots_per_task: 3
      });
      setRecommendations(recs);
      const status = await api.getAIStatus();
      setModelStatus(status);
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setGenLoading(false);
    }
  };

  const openFeedbackModal = (rec: Recommendation, action: 'accept' | 'reject') => {
    setActiveRec(rec);
    setFeedbackAction(action);
    setFeedbackNote('');
    setActionError(null);
  };

  const handleConfirmAction = async () => {
    if (!activeRec) return;
    try {
      setActionLoading(true);
      setActionError(null);

      if (feedbackAction === 'accept') {
        await api.acceptRecommendation(activeRec.id, feedbackNote || undefined);
      } else {
        await api.rejectRecommendation(activeRec.id, feedbackNote || undefined);
      }

      setActiveRec(null);
      await loadData();
    } catch (err: any) {
      setActionError(err.message || 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">AI Scheduling Suggestions</h1>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-violet-600/20 text-violet-300 border border-violet-500/30">
              Increment 2
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-0.5">
            Machine-learning ranked recommendations based on task features, student fatigue, and prime study hours.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            disabled={genLoading}
            onClick={handleGenerate}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white text-xs font-semibold flex items-center space-x-2 shadow-lg shadow-violet-600/25 transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${genLoading ? 'animate-spin' : ''}`} />
            <span>{genLoading ? 'Evaluating Slots...' : 'Generate AI Suggestions'}</span>
          </button>
        </div>
      </div>

      {/* Model Status & Telemetry Card */}
      {modelStatus && (
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900/90 via-violet-950/20 to-slate-900/90">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="font-bold text-sm text-slate-100">{modelStatus.model_type}</h3>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-violet-400">
                    {modelStatus.model_version}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">{modelStatus.status_detail}</p>
              </div>
            </div>

            <div className="flex items-center space-x-6 text-xs text-slate-300">
              {modelStatus.test_accuracy && (
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Accuracy</span>
                  <span className="font-bold text-emerald-400 text-sm">
                    {(modelStatus.test_accuracy * 100).toFixed(1)}%
                  </span>
                </div>
              )}
              {modelStatus.test_roc_auc && (
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">ROC-AUC</span>
                  <span className="font-bold text-sky-400 text-sm">
                    {modelStatus.test_roc_auc.toFixed(3)}
                  </span>
                </div>
              )}
              {modelStatus.training_sample_count && (
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Dataset Size</span>
                  <span className="font-bold text-indigo-400 text-sm">
                    {modelStatus.training_sample_count} samples
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="mt-3 flex items-start space-x-2 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5 text-slate-500 flex-shrink-0 mt-0.5" />
            <p>
              <strong className="text-slate-300">Notice:</strong> Model scores are statistical estimates, not guarantees.
              Candidate slots are filtered strictly against your availability windows, task deadlines, and daily maximum study limits.
            </p>
          </div>
        </div>
      )}

      {/* Recommendations Cards */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs">
          <div className="w-8 h-8 border-3 border-violet-500/20 border-t-violet-500 rounded-full animate-spin mx-auto mb-2" />
          Loading AI recommendations...
        </div>
      ) : recommendations.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl border border-slate-800 text-center">
          <Sparkles className="w-10 h-10 text-violet-400/80 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-200">No pending AI suggestions</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Click "Generate AI Suggestions" above to evaluate candidate slots for incomplete tasks across your schedule.
          </p>
          <button
            disabled={genLoading}
            onClick={handleGenerate}
            className="mt-4 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold inline-flex items-center space-x-1.5"
          >
            <Sparkles className="w-4 h-4" />
            <span>Generate Suggestions Now</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recommendations.map((rec) => {
            const startD = new Date(rec.recommended_start_at);
            const endD = new Date(rec.recommended_end_at);
            const scorePct = rec.suitability_score !== null && rec.suitability_score !== undefined
              ? Math.round(rec.suitability_score * 100)
              : 50;

            return (
              <div
                key={rec.id}
                className="glass-card p-5 rounded-2xl border border-slate-800 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span
                      className="px-2 py-0.5 rounded text-[10px] font-bold"
                      style={{
                        backgroundColor: `${rec.subject_color || '#3B82F6'}20`,
                        color: rec.subject_color || '#3B82F6',
                        border: `1px solid ${rec.subject_color || '#3B82F6'}40`
                      }}
                    >
                      {rec.subject_name || 'Subject'}
                    </span>

                    {/* Suitability Badge */}
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30">
                      {scorePct}% Match
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-100 text-sm">{rec.task_title}</h3>

                  {/* Slot Details */}
                  <div className="mt-3 p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-xs space-y-1.5">
                    <div className="flex items-center space-x-2 text-slate-300 font-medium">
                      <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                      <span>{startD.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</span>
                    </div>
                    <div className="flex items-center space-x-2 text-slate-300 font-medium">
                      <Clock className="w-3.5 h-3.5 text-indigo-400" />
                      <span>
                        {startD.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} –{' '}
                        {endD.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>

                  {/* Feature Explanation */}
                  <div className="mt-3 text-[11px] text-slate-400 leading-relaxed">
                    <span className="font-semibold text-slate-300">Model Insight: </span>
                    {rec.explanation}
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <button
                    onClick={() => openFeedbackModal(rec, 'reject')}
                    className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-rose-950/40 text-slate-400 hover:text-rose-300 border border-slate-700/60 hover:border-rose-800/50 text-xs font-medium flex items-center space-x-1.5 transition-colors"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                    <span>Decline</span>
                  </button>

                  <button
                    onClick={() => openFeedbackModal(rec, 'accept')}
                    className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-md shadow-indigo-600/20 transition-all"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                    <span>Accept Slot</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Confirmation & Feedback Modal */}
      <Modal
        isOpen={activeRec !== null}
        onClose={() => setActiveRec(null)}
        title={feedbackAction === 'accept' ? 'Accept AI Recommendation' : 'Decline Recommendation'}
        maxWidth="max-w-md"
      >
        {activeRec && (
          <div className="space-y-4 text-xs">
            {actionError && (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300">
                {actionError}
              </div>
            )}

            <p className="text-slate-300">
              {feedbackAction === 'accept'
                ? `Accepting this slot will re-validate conflicts and save a scheduled study session for "${activeRec.task_title}".`
                : `Declining will record your preference for future model evaluations without changing your saved schedule.`}
            </p>

            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Optional Feedback / Reason
              </label>
              <textarea
                rows={2}
                value={feedbackNote}
                onChange={(e) => setFeedbackNote(e.target.value)}
                placeholder={feedbackAction === 'accept' ? 'e.g. Good time of day' : 'e.g. Conflicts with club meeting'}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setActiveRec(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={actionLoading}
                onClick={handleConfirmAction}
                className={`px-4 py-2 rounded-xl text-white font-semibold flex items-center space-x-1.5 ${
                  feedbackAction === 'accept'
                    ? 'bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/25'
                    : 'bg-rose-600 hover:bg-rose-500'
                }`}
              >
                <span>{actionLoading ? 'Processing...' : feedbackAction === 'accept' ? 'Confirm & Schedule' : 'Confirm Decline'}</span>
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
