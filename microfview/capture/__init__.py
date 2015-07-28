import os.path

def get_capture_object(desc, **options):
    desc = desc or ''   #remove None
    if os.path.isfile(desc):
        if desc.endswith('.fmf'):
            from .videofmf import FMFCapture
            return FMFCapture(desc, **options)
        else:
            from .opencv import OpenCVCapture
            return OpenCVCapture(desc)
    elif desc.startswith('/dev/video'):
        raise Exception("opencv device not implemented")
    else:
        from .cameracamiface import CamifaceCapture
        return CamifaceCapture(**options)
        
    
