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
  image?: string
  student_count?: number
  faculty_count?: number
  national_rank?: number
  world_rank?: number
  is_verified?: boolean
  founded_year?: number
  admission_rate?: number
  created_at?: string
  updated_at?: string
  majors?: Major[]
  admission_scores?: AdmissionScore[]
  is_favorited?: boolean
  board_id?: number
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

export type PlaceCategory =
  | 'landmark'
  | 'building'
  | 'dormitory'
  | 'canteen'
  | 'library'
  | 'sport'
  | 'activity'
  | 'scenic'
  | 'other'

export interface Place {
  id: number
  name: string
  school: string | number
  category: PlaceCategory
  category_display: string
  latitude: number
  longitude: number
  description?: string
  address?: string
  icon?: string
  is_active?: boolean
  checkin_count: number
  is_checked_in_today?: boolean
  distance?: number
  created_at?: string
  updated_at?: string
}

export interface CheckIn {
  id: number
  place: Place
  latitude: number
  longitude: number
  note?: string
  created_at: string
}

export interface NearbyPlaceParams {
  lat: number
  lng: number
  radius?: number
  school_id?: number
  category?: PlaceCategory
}

export interface NearbyEventParams {
  lat?: number
  lng?: number
  radius?: number
  school_id?: number
}

export interface PlaceParams {
  school_id?: number
  category?: PlaceCategory
}