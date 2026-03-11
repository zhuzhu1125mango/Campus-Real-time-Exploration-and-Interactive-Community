import { DefineComponent } from 'vue'
import Cropper from 'cropperjs'

declare module 'vue-cropperjs' {
  const VueCropper: DefineComponent<{
    src: string
    alt?: string
    imgStyle?: object
    dragMode?: string
    responsive?: boolean
    restore?: boolean
    checkCrossOrigin?: boolean
    checkOrientation?: boolean
    modal?: boolean
    guides?: boolean
    center?: boolean
    highlight?: boolean
    background?: boolean
    autoCrop?: boolean
    autoCropArea?: number
    movable?: boolean
    rotatable?: boolean
    scalable?: boolean
    zoomable?: boolean
    zoomOnTouch?: boolean
    zoomOnWheel?: boolean
    wheelZoomRatio?: number
    cropBoxMovable?: boolean
    cropBoxResizable?: boolean
    toggleDragModeOnDblclick?: boolean
    minContainerWidth?: number
    minContainerHeight?: number
    minCanvasWidth?: number
    minCanvasHeight?: number
    minCropBoxWidth?: number
    minCropBoxHeight?: number
    viewMode?: number
    aspectRatio?: number
  }, {}, any> & {
    replace: (url: string) => void
    reset: () => void
    clear: () => void
    initCrop: () => void
    getCropBoxData: () => Cropper.CropBoxData
    setCropBoxData: (data: Cropper.CropBoxData) => void
    getCropperCanvas: (options?: Cropper.GetCroppedCanvasOptions) => HTMLCanvasElement
    getCroppedCanvas: (options?: Cropper.GetCroppedCanvasOptions) => HTMLCanvasElement
    setDragMode: (mode: Cropper.DragMode) => void
    zoom: (ratio: number) => void
    move: (offsetX: number, offsetY?: number) => void
    moveTo: (x: number, y?: number) => void
    rotate: (degree: number) => void
    rotateTo: (degree: number) => void
    scaleX: (scaleX: number) => void
    scaleY: (scaleY: number) => void
    scale: (scaleX: number, scaleY?: number) => void
    getData: (rounded?: boolean) => Cropper.Data
    setData: (data: Partial<Cropper.Data>) => void
    getContainerData: () => Cropper.ContainerData
    getImageData: () => Cropper.ImageData
    getCanvasData: () => Cropper.CanvasData
    setCanvasData: (data: Partial<Cropper.CanvasData>) => void
    setCropBoxData: (data: Partial<Cropper.CropBoxData>) => void
    getCropBoxData: () => Cropper.CropBoxData
    setAspectRatio: (aspectRatio: number) => void
    setDragMode: (mode: string) => void
  }

  export default VueCropper
} 