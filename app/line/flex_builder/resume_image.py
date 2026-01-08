def build_quick_resume_image_flex():
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "0px",
            "contents": [
                {
                    "type": "image",
                    "url": "https://pub-1e15d55216a149c193d07024bf1d5269.r2.dev/screenshots/resume.png",
                    "size": "full",
                    "aspectMode": "fit",
                    "aspectRatio": "2:3",
                    "action": {
                        "type": "uri",
                        "uri": "https://drive.google.com/file/d/1Pu2321lWagtWPOlhmKCY8qh0fLT9g0kO/view?usp=sharing"
                    }
                }
            ]
        }
    }
