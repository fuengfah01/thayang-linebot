# flex/messages.py — ใช้ map_url แทน lat/lng

def _map_uri(obj):
    """ดึง map_url ถ้ามี ไม่มีใช้ lat/lng fallback"""
    if obj.get("map_url"):
        return obj["map_url"]
    lat = obj.get("lat", "")
    lng = obj.get("lng", "")
    if lat and lng:
        return f"https://maps.google.com/?q={lat},{lng}"
    return "https://maps.google.com/?q=ท่ายาง+เพชรบุรี"


def place_bubble(p):
    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": p.get("cover_image") or "https://via.placeholder.com/400x200",
            "size": "full", "aspectRatio": "20:13", "aspectMode": "cover"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": p["place_name"], "weight": "bold", "size": "lg", "wrap": True},
                {"type": "text", "text": p.get("highlight") or p.get("place_description") or "",
                 "size": "sm", "color": "#666666", "wrap": True, "maxLines": 3},
                {"type": "separator"},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text",
                     "text": "🕐 " + str(p.get("open_time") or "08:00")[:5] + " - " + str(p.get("close_time") or "17:00")[:5],
                     "size": "xs", "color": "#888888", "flex": 1},
                ]},
            ]
        },
        "footer": {
            "type": "box", "layout": "horizontal", "spacing": "sm",
            "contents": [
                {
                    "type": "button", "style": "primary", "height": "sm",
                    "action": {"type": "message", "label": "📍 รายละเอียด", "text": f"รายละเอียด{p['place_name']}"}
                },
                {
                    "type": "button", "style": "secondary", "height": "sm",
                    "action": {"type": "uri", "label": "🗺 แผนที่", "uri": _map_uri(p)}
                },
            ]
        }
    }


def place_detail_bubble(p, images):
    img_url = p.get("cover_image") or "https://via.placeholder.com/400x200"
    if images:
        raw = images[0].get("image_path", "")
        if raw and raw.startswith("http"):
            img_url = raw

    return {
        "type": "bubble", "size": "giga",
        "hero": {
            "type": "image", "url": img_url,
            "size": "full", "aspectRatio": "20:13", "aspectMode": "cover"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": p["place_name"], "weight": "bold", "size": "xl", "wrap": True},
                {"type": "text", "text": "📖 ประวัติ", "weight": "bold", "size": "sm", "color": "#1a7a4a"},
                {"type": "text", "text": p.get("place_description") or "",
                 "size": "sm", "color": "#555555", "wrap": True},
                {"type": "separator"},
                {"type": "text", "text": "⭐ จุดเด่น", "weight": "bold", "size": "sm", "color": "#1a7a4a"},
                {"type": "text", "text": p.get("highlight") or "",
                 "size": "sm", "color": "#555555", "wrap": True},
                {"type": "separator"},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "🕐 เวลาเปิด", "size": "sm", "flex": 1, "color": "#888888"},
                    {"type": "text",
                     "text": str(p.get("open_time","08:00"))[:5] + " - " + str(p.get("close_time","17:00"))[:5],
                     "size": "sm", "flex": 2},
                ]},
            ]
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": [
                {
                    "type": "button", "style": "primary", "height": "sm",
                    "action": {"type": "uri", "label": "🗺 เปิดแผนที่", "uri": _map_uri(p)}
                },
            ]
        }
    }


def restaurant_bubble(r):
    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": r.get("cover_image") or "https://via.placeholder.com/400x200",
            "size": "full", "aspectRatio": "20:13", "aspectMode": "cover"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": r["name"], "weight": "bold", "size": "lg", "wrap": True},
                {"type": "text", "text": f"🍽 {r['category']}", "size": "xs", "color": "#1a7a4a"},
                {"type": "text", "text": r.get("highlight") or "",
                 "size": "sm", "color": "#666666", "wrap": True, "maxLines": 3},
                {"type": "separator"},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text",
                     "text": f"🕐 {str(r.get('open_hours','?'))[:5]} - {str(r.get('close_hours','?'))[:5]}",
                     "size": "xs", "color": "#888888", "flex": 1},
                ]},
            ]
        },
        "footer": {
            "type": "box", "layout": "horizontal", "spacing": "sm",
            "contents": [
                {
                    "type": "button", "style": "primary", "height": "sm",
                    "action": {"type": "uri", "label": "🗺 แผนที่", "uri": _map_uri(r)}
                },
                {
                    "type": "button", "style": "secondary", "height": "sm",
                    "action": {"type": "message", "label": "📋 รายละเอียด", "text": f"ข้อมูลร้าน{r['name']}"}
                },
            ]
        }
    }


def souvenir_bubble(s):
    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": s.get("cover_image") or "https://via.placeholder.com/400x200",
            "size": "full", "aspectRatio": "20:13", "aspectMode": "cover"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": s["name"], "weight": "bold", "size": "lg", "wrap": True},
                {"type": "text", "text": s.get("description") or "",
                 "size": "sm", "color": "#666666", "wrap": True, "maxLines": 3},
                {"type": "separator"},
                {"type": "box", "layout": "vertical", "spacing": "xs", "contents": [
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "📞", "size": "xs", "flex": 0},
                        {"type": "text", "text": s.get("phone") or "-",
                         "size": "xs", "color": "#888888", "flex": 1, "margin": "sm"},
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "🕐", "size": "xs", "flex": 0},
                        {"type": "text",
                         "text": f"{str(s.get('open_hours','?'))[:5]} - {str(s.get('close_hours','?'))[:5]}",
                         "size": "xs", "color": "#888888", "flex": 1, "margin": "sm"},
                    ]},
                ]},
            ]
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": [
                {
                    "type": "button", "style": "primary", "height": "sm",
                    "action": {"type": "uri", "label": "🗺 แผนที่", "uri": _map_uri(s)}
                },
            ]
        }
    }


def activity_bubble(activity_type, places):
    emoji_map = {"ไหว้พระ": "🙏", "ถ่ายรูป": "📸", "ให้อาหารปลา": "🐟", "ตะลอนกิน": "🍜"}
    emoji = emoji_map.get(activity_type, "🧭")

    place_items = []
    for p in places:
        place_items.append({
            "type": "box", "layout": "horizontal", "spacing": "sm",
            "contents": [
                {"type": "text", "text": "•", "size": "sm", "flex": 0},
                {"type": "text", "text": p.get("place_name") or p.get("name",""),
                 "size": "sm", "flex": 1, "wrap": True},
                {
                    "type": "button", "style": "link", "height": "sm", "flex": 0,
                    "action": {"type": "uri", "label": "แผนที่", "uri": _map_uri(p)}
                },
            ]
        })

    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#1a7a4a",
            "contents": [
                {"type": "text", "text": f"{emoji} {activity_type}",
                 "color": "#ffffff", "weight": "bold", "size": "lg"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": "สถานที่แนะนำ", "weight": "bold", "size": "md"},
                {"type": "separator"},
                *place_items
            ]
        }
    }


def about_bubbles(sections):
    label_map = {
        "highlight": ("⭐", "จุดเด่น",    "#1a7a4a"),
        "lifestyle":  ("🌾", "วิถีชีวิต",  "#8B6914"),
        "culture":    ("🏛", "วัฒนธรรม",  "#4A148C"),
        "contact":    ("📞", "ติดต่อเรา", "#0277BD"),
    }
    bubbles = []
    for s in sections:
        icon, title, color = label_map.get(s["section"], ("ℹ️", s["section"], "#333333"))
        bubbles.append({
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": color,
                "contents": [
                    {"type": "text", "text": f"{icon} {title}",
                     "color": "#ffffff", "weight": "bold", "size": "lg"}
                ]
            },
            "body": {
                "type": "box", "layout": "vertical",
                "contents": [
                    {"type": "text", "text": s.get("content") or "",
                     "size": "sm", "wrap": True, "color": "#333333"}
                ]
            }
        })
    return bubbles


def carousel(bubbles):
    return {
        "type": "flex",
        "altText": "ข้อมูลจากท่ายาง",
        "contents": {"type": "carousel", "contents": bubbles}
    }


def flex_message(bubble):
    return {
        "type": "flex",
        "altText": "ข้อมูลจากท่ายาง",
        "contents": bubble
    }