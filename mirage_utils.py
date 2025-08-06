class MirageImageUtils:
    """
    Utility class for image file operations and user input for the MIRAGE pipeline.
    """
    import os
    from datetime import datetime

    @staticmethod
    def get_latest_image(folder="/content/"):
        import os
        images = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            raise FileNotFoundError("No image files found in the specified folder.")
        latest_image = max(images, key=os.path.getmtime)
        return latest_image

    @staticmethod
    def get_user_prompt():
        return input("Enter your edit instruction (e.g., 'replace tiger with lion'): ")

    @staticmethod
    def save_and_show_result(result, output_path="/content/edited_image.png"):
        result.save(output_path)
        print(f"✅ Edited image saved at: {output_path}")
        result.show()
