import os
import shutil
import json
import zipfile
from io import BytesIO
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.photo_dumper import PhotoDumper
from utils.cleanup import remove_temp_files, clear_directory

UPLOADS_DIR = "uploads"  # Main directory for all uploaded files
OUTPUT_DIR = "output"    # Directory for processed results

def setup_directories():
    """Create necessary directories and remove redundant ones."""
    # Create only necessary directories
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Remove redundant directories if they exist
    redundant_dirs = ['temp_album', 'temp_uploads', 'album']
    for dir_name in redundant_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

setup_directories()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get absolute paths
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / UPLOADS_DIR
OUTPUT_DIR = BASE_DIR / OUTPUT_DIR

# Mount static files with proper cache control
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR), check_dir=False), name="uploads")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR), check_dir=False), name="output")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

@app.middleware("http")
async def file_serving_middleware(request: Request, call_next):
    """Middleware to ensure files are properly served during cleanup operations"""
    response = await call_next(request)
    
    # Handle 404s for image files that should exist
    if (response.status_code == 404 and 
        (request.url.path.startswith("/uploads/") or request.url.path.startswith("/output/")) and
        any(request.url.path.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp'))):
        
        # If we have results, ensure the file exists
        if manager.has_results:
            file_path = BASE_DIR / request.url.path.lstrip("/")
            if file_path.exists():
                return FileResponse(file_path)
    
    return response


@app.get("/")
async def root():
    """Root endpoint that serves the frontend without cleaning files"""
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.post("/init-cleanup")
async def init_cleanup():
    """Optional initial cleanup endpoint that can be called when needed"""
    try:
        # Only clean if no active process or results
        if not manager.processing and not manager.has_results:
            clear_directory(UPLOADS_DIR)
            clear_directory(OUTPUT_DIR)
            
            temp_paths = [
                "temp_album",
                "temp_uploads",
                "album",
                "uploads/categories.txt",
            ]
            
            remove_temp_files(BASE_DIR, temp_paths)
            
        return JSONResponse({"message": "Initialization complete"})
    except Exception as e:
        print(f"Init cleanup error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.processing = False
        self._last_status = None
        self.has_results = False  # Track if we have processed results
        self._cleanup_lock = False  # Add lock to prevent concurrent cleanups

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        if self._last_status:
            try:
                await websocket.send_json(self._last_status)
            except WebSocketDisconnect:
                await self.handle_disconnect(websocket)

    async def handle_disconnect(self, websocket: WebSocket):
        self.disconnect(websocket)
        # Only clean up if this was the last connection and no results exist
        if not self.active_connections and not self.has_results:
            if self.processing:
                self.stop_processing()
            await self.cleanup_temp_files()

    async def cleanup_temp_files(self):
        """Clean only temporary processing files, not selected images"""
        if self._cleanup_lock:
            return
            
        try:
            self._cleanup_lock = True
            if not self.has_results:  # Only clean if no results
                temp_paths = [
                    "temp_album",
                    "temp_uploads",
                    "album",
                    "uploads/",
                ]
                clear_directory(BASE_DIR, temp_paths)
        finally:
            self._cleanup_lock = False

    def reset_state(self):
        """Reset all state variables"""
        self.processing = False
        self._last_status = None
        self.has_results = False
        self._cleanup_lock = False

    def set_has_results(self, value: bool):
        """Update the results state"""
        self.has_results = value

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        self._last_status = message
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    def start_processing(self):
        self.processing = True

    def stop_processing(self):
        self.processing = False
        self._last_status = None

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.handle_disconnect(websocket)

@app.post("/upload")
async def upload_photos(request: Request, files: List[UploadFile] = File(...)):
    """Handle individual file uploads"""
    try:
        saved_paths = []
        skipped_files = []
        
        for file in files:
            if not file.filename:
                continue
            
            # Only process image files
            if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                continue
                
            file_path = UPLOADS_DIR / file.filename
            # Skip if file already exists
            if file_path.exists():
                skipped_files.append(file.filename)
                continue
                
            # Save file
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            saved_paths.append(str(file_path))
        
        return JSONResponse({
            "message": f"Successfully uploaded {len(saved_paths)} files",
            "uploaded": len(saved_paths),
            "files": [os.path.basename(p) for p in saved_paths],
            "skipped": len(skipped_files),
            "skipped_files": skipped_files
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/upload-folder")
async def upload_folder(folder_path: str = Form(...)):
    """Handle folder uploads by copying image files to uploads directory"""
    try:
        if not os.path.exists(folder_path):
            return JSONResponse({"error": "Path does not exist"}, status_code=404)

        copied_files = []
        skipped_files = []
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                src = os.path.join(folder_path, filename)
                dst = os.path.join(UPLOADS_DIR, filename)
                # Skip if file already exists
                if os.path.exists(dst):
                    skipped_files.append(filename)
                    continue
                shutil.copy2(src, dst)
                copied_files.append(filename)

        return JSONResponse({
            "message": f"Successfully copied {len(copied_files)} images",
            "files": copied_files,
            "skipped": len(skipped_files),
            "skipped_files": skipped_files
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/categories")
async def get_categories():
    """Generate category list automatically"""
    category_file = "defaults/photodump_list.txt"
    categories = ["None"]  # Add None category at index 0
    with open(category_file, "r") as f:
        for line in f:
            category = line.strip()
            if '. ' in category:
                category = category.split('. ')[1]
            categories.append(category)
    return categories

@app.post("/process")
async def process_photos(request: Request):
    """Process uploaded photos"""
    try:
        if manager.processing:
            return JSONResponse(
                {"error": "Processing already in progress"}, 
                status_code=409
            )

        manager.start_processing()
        body = await request.json()
        categories = body if isinstance(body, list) else []

        # Create temporary categories file
        categories_text = "\n".join(f"{i+1}. {cat}" for i, cat in enumerate(categories))
        categories_file = os.path.join(UPLOADS_DIR, "categories.txt")
        with open(categories_file, "w") as f:
            f.write(categories_text)

        # Initialize photo dumper with the uploads directory
        dumper = PhotoDumper(
            album_path=str(UPLOADS_DIR),
            categories_file=categories_file,
            batch_size=4,
            pre_filter=100,
            keep_top_k=1,
            output_dir=str(OUTPUT_DIR)
        )

        await manager.broadcast({"status": "categorizing"})
        ranked_categories = dumper.process()
        
        # Mark that we have results to prevent premature cleanup
        manager.set_has_results(True)
        
        await manager.broadcast({
            "status": "complete",
            "results": ranked_categories
        })

        manager.stop_processing()
        return JSONResponse(ranked_categories)
    except Exception as e:
        manager.stop_processing()
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/download")
async def download_selection():
    """Copy all images from OUTPUT_DIR to the user's Downloads/photodump folder"""
    # user's download folder
    home = Path.home()
    OUTPUT_FOLDER = home / "Downloads"
    ZIP_FILENAME = "images.zip"
    zip_path = os.path.join(OUTPUT_FOLDER, ZIP_FILENAME)

    # Create ZIP file
    # assert output dir is not empty 
    assert os.path.exists(OUTPUT_DIR) and os.listdir(OUTPUT_DIR), "No images to download"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(OUTPUT_DIR):
            for file in files:
                if file.endswith((".png", ".jpg", ".jpeg")):
                    zipf.write(os.path.join(root, file), file)

    # Serve the ZIP file for download
    return FileResponse(zip_path, filename="images.zip", media_type="application/zip")
    
@app.post("/clear")
async def clear_data():
    """Clear all data including results"""
    try:
        if manager.processing:
            await manager.broadcast({"status": "cancelled"})
            manager.stop_processing()

        # Clear main directories
        downloads_dir = BASE_DIR / "downloads"
        if downloads_dir.exists():
            clear_directory(downloads_dir)
            # Remove the downloads directory itself
            try:
                downloads_dir.rmdir()
            except:
                pass
                
        clear_directory(UPLOADS_DIR)
        clear_directory(OUTPUT_DIR)
        
        # Clear all temporary files
        temp_paths = [
            "temp_album",
            "temp_uploads",
            "album",
            "downloads",
            "uploads/categories.txt",
            "output/category_results.json",
            "output/category_list.json",
            "output/ranked_categories.json"
        ]
        
        remove_temp_files(BASE_DIR, temp_paths)
        
        # Reset results state
        manager.set_has_results(False)
        
        await manager.broadcast({"status": "cleared"})    
        return JSONResponse({"message": "All data cleared successfully"})
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to clear data: {str(e)}"}, 
            status_code=500
        )

@app.get("/list-uploads")
async def list_uploads():
    """List all files in the uploads directory"""
    try:
        files = []
        for item in UPLOADS_DIR.iterdir():
            if item.is_file() and item.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                files.append(item.name)
        return files
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/remove-file")
async def remove_file(request: Request):
    """Remove a specific file from uploads directory"""
    try:
        body = await request.json()
        filename = body.get("filename")
        if not filename:
            return JSONResponse({"error": "No filename provided"}, status_code=400)
        
        file_path = UPLOADS_DIR / filename
        if file_path.exists():
            file_path.unlink()
            return JSONResponse({"message": "File removed successfully"})
        return JSONResponse({"error": "File not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/clear-uploads")
async def clear_uploads():
    """Clear all files from uploads directory"""
    try:
        clear_directory(UPLOADS_DIR)
        # Only remove image files, keep other system files
        for item in UPLOADS_DIR.iterdir():
            if item.is_file() and item.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                item.unlink()
        return JSONResponse({"message": "Uploads cleared successfully"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/cleanup")
async def cleanup_on_unload():
    """Handle cleanup when page is unloaded or refreshed"""
    try:
        # Only clean up if we don't have results
        if not manager.has_results:
            if manager.processing:
                manager.stop_processing()
                await manager.broadcast({"status": "cancelled"})
            
            # Clear only temporary files
            await manager.cleanup_temp_files()
        return JSONResponse({"message": "Cleanup handled"})
    except Exception as e:
        print(f"Cleanup error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        # Ensure processing state is reset even if cleanup fails
        manager.processing = False
        manager._last_status = None

# Serve frontend files
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # If no path specified, serve index.html
    if not full_path:
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    
    # Check for specific files
    requested_path = FRONTEND_DIR / full_path
    if requested_path.exists():
        return FileResponse(str(requested_path))
    
    # Fallback to index.html for client-side routing
    return FileResponse(str(FRONTEND_DIR / "index.html"))

if __name__ == '__main__':
    import uvicorn
    setup_directories()
    uvicorn.run(app, host="0.0.0.0", port=8000)