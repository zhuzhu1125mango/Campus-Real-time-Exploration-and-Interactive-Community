import type { User } from './user'

export interface Category {
  id: number
  name: string
  parent: string | null
  description: string
  order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Course {
  id: number
  title: string
  slug: string
  description: string
  instructor: User
  categories: Category[]
  cover_image: string | null
  price: number
  is_free: boolean
  is_published: boolean
  publish_date: string | null
  enroll_count: number
  view_count: number
  average_rating: number
  chapter_count: number
  lesson_count: number
  created_at: string
  updated_at: string
}

export interface Chapter {
  id: number
  course: string
  title: string
  description: string
  order: number
  lesson_count: number
  created_at: string
  updated_at: string
}

export interface Lesson {
  id: number
  course: string
  chapter: string
  title: string
  description: string
  content: string
  video_url: string
  duration: string | null
  is_free: boolean
  order: number
  view_count: number
  created_at: string
  updated_at: string
}

export interface Enrollment {
  id: number
  user: User
  course: Course
  is_completed: boolean
  progress: number
  enrolled_at: string
  completed_at: string | null
}

export interface Progress {
  id: number
  enrollment: string
  lesson: Lesson
  is_completed: boolean
  last_watched_at: string | null
  watched_duration: number
}

export interface Review {
  id: number
  user: User
  course: string
  rating: number
  comment: string
  is_approved: boolean
  created_at: string
  updated_at: string
}

export interface LearningResource {
  id: number
  course: string
  title: string
  description: string
  file_url: string
  file_type: string
  file_size: number
  download_count: number
  is_free: boolean
  created_at: string
  updated_at: string
}