/**
 * LIMS TypeScript Type Definitions
 *
 * Энэ файл нь LIMS системийн TypeScript төрлүүдийг тодорхойлно.
 */

// ============================================================
// Sample Types
// ============================================================

export interface Sample {
  id: number
  sample_code: string
  client_name: string | null
  sample_type: string | null
  received_date: string
  status: SampleStatus
  weight: number | null
  notes: string | null
}

export type SampleStatus = 'new' | 'in_progress' | 'completed' | 'archived' | 'disposed'

// ============================================================
// Analysis Types
// ============================================================

export interface AnalysisResult {
  id: number
  sample_id: number
  analysis_code: string
  final_result: number | null
  status: AnalysisStatus
  raw_data: Record<string, number> | null
  created_at: string
  updated_at: string
}

export type AnalysisStatus = 'pending_review' | 'approved' | 'rejected' | 'reanalysis'

export interface AnalysisType {
  code: string
  name: string
  unit: string
  required_role: string
}

// ============================================================
// API Response Types
// ============================================================

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  has_next: boolean
  has_prev: boolean
}

// ============================================================
// Form Types
// ============================================================

export interface AnalysisFormData {
  sample_id: number
  analysis_code: string
  raw_data: Record<string, number>
  final_result?: number
}

// ============================================================
// Utility Types
// ============================================================

export type Nullable<T> = T | null

export type DateString = string // ISO 8601 format: YYYY-MM-DD

export type TimeString = string // HH:MM:SS format

// ============================================================
// Window Extensions (global LIMS namespace)
// ============================================================

declare global {
  interface Window {
    LIMS: {
      getShiftDate: () => string
      getCsrfToken: () => string
      toast: (message: string, type?: 'info' | 'success' | 'warning' | 'danger') => void
    }
    getShiftDate: () => string
    DEBUG: boolean
    bootstrap: typeof import('bootstrap')
  }
}
