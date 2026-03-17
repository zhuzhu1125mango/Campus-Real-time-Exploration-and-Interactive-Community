import type { User } from './user'

export interface School {
  id: number
  name: string
  english_name?: string
  code?: string
  abbreviation?: string
  school_type?: string
  school_level?: string
  province: string
  city?: string
  address?: string
  location?: string
  website?: string
  email?: string
  phone?: string
  admission_office_phone?: string
  admission_office_email?: string
  has_graduate_program?: boolean
  introduction?: string
  features?: string
  facilities?: string
  logo?: string
  banner?: string
  student_count?: number
  faculty_count?: number
  national_rank?: number
  world_rank?: number
  is_verified?: boolean
  founded_year?: number
  created_at?: string
  updated_at?: string
  majors?: Major[]
  admission_scores?: AdmissionScore[]
  admission_rate?: number
}

export interface Major {
  id: number
  name: string
  code: string
  description: string
  employment_rate: number
  avg_salary: number
}

export interface AdmissionScore {
  id: number
  year: number
  province: string
  science: number
  arts: number
}

export interface SchoolListResponse {
  count: number
  next: string | null
  previous: string | null
  results: School[]
}

export interface SchoolQueryParams {
  page?: number
  pageSize?: number
  search?: string
  province?: string
  city?: string
  school_type?: string
  school_level?: string
  sort_by?: string
}

export interface SchoolFilterData {
  provinces: string[]
  schoolTypes: { [key: string]: string }
  schoolLevels: { [key: string]: string }
}

export interface SchoolCardProps {
  school: School
  showDetails?: boolean
  showActions?: boolean
}

export interface SchoolRating {
  id: number
  school: number
  user: User
  rating: number
  comment: string
  created_at: string
}

export interface SchoolRatingResponse {
  count: number
  results: SchoolRating[]
}

export interface ImportCsvResponse {
  success_count: number
  error_count: number
  total: number
  errors?: string[]
}

export interface Event {
  id: number
  title: string
  description: string
  start_time: string
  end_time: string
  location: string
  organizer: string
  capacity: number
  status: string
  school: number
  created_at: string
  updated_at: string
}

export interface EventListResponse {
  count: number
  results: Event[]
}

export interface Post {
  id: number
  title: string
  content: string
  author: {
    username: string
  }
  comments_count: number
  likes_count: number
  views: number
  tags?: string[]
}

export interface RecommendationResponse {
  recommendations: any[]
  reasoning: string[]
}