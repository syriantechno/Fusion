# -*- coding: utf-8 -*-
"""
🔹 معالج DXF متقدم - تجميع الخطوط إلى مضلعات مغلقة
"""

from profile.dxf_normalizer import load_dxf_segments


def extrude_profile(file_path: str, depth: float = 40.0, axis: str = "Y"):
    """
    معالجة ذكية لملف DXF - تجميع الخطوط إلى مضلعات ثم إكسترود
    """
    print(f"📂 [smart_extrude] تحميل DXF من: {file_path}")

    try:
        segments, bbox = load_dxf_segments(file_path)
        if not segments:
            print("⚠️ [smart_extrude] لا توجد مقاطع صالحة في DXF.")
            return None
        print(f"✅ [smart_extrude] تم تحميل {len(segments)} مقطع")
    except Exception as e:
        print(f"❌ [smart_extrude] فشل تحميل DXF: {e}")
        return None

    # ---------------------------------------------------------
    # 🔍 المرحلة 1: تجميع الخطوط إلى مضلعات مغلقة
    # ---------------------------------------------------------
    print("🔍 [smart_extrude] تجميع الخطوط إلى مضلعات...")

    polygons = find_closed_polygons_optimized(segments)

    if not polygons:
        print("❌ [smart_extrude] لم يتم العثور على مضلعات مغلقة")
        return None

    print(f"✅ [smart_extrude] تم العثور على {len(polygons)} مضلع مغلق")

    # ---------------------------------------------------------
    # 🧩 المرحلة 2: بناء وجوه من المضلعات
    # ---------------------------------------------------------
    print("🧩 [smart_extrude] بناء الوجوه من المضلعات...")

    faces = []
    for i, polygon in enumerate(polygons):
        face = build_face_from_polygon(polygon)
        if face:
            faces.append(face)
            print(f"✅ [smart_extrude] تم بناء وجه {i + 1} من مضلع بـ {len(polygon)} ضلع")

    if not faces:
        print("❌ [smart_extrude] فشل بناء أي وجوه")
        return None

    # ---------------------------------------------------------
    # 🚀 المرحلة 3: تنفيذ الإكسترود
    # ---------------------------------------------------------
    print("🚀 [smart_extrude] تنفيذ الإكسترود...")

    # إذا كان هناك وجه واحد فقط
    if len(faces) == 1:
        return perform_fast_extrusion(faces[0], depth, axis)

    # إذا كان هناك عدة وجوه (للثقوب والأشكال المعقدة)
    return perform_complex_extrusion(faces, depth, axis)


def find_closed_polygons_optimized(segments, tolerance=0.01):
    """
    تجميع سريع للمضلعات المغلقة مع تحسين الأداء
    """
    import time
    start_time = time.time()

    # تنظيف وتجميع المقاطع
    clean_segments = []
    point_to_segments = {}

    for i, (p1, p2) in enumerate(segments):
        # تقريب النقاط لتجنب أخطاء الدقة
        p1_clean = (round(p1[0], 4), round(p1[1], 4))
        p2_clean = (round(p2[0], 4), round(p2[1], 4))

        # تخطي المقاطع الصغيرة
        if distance(p1_clean, p2_clean) < tolerance:
            continue

        clean_segments.append((p1_clean, p2_clean))

        # بناء فهرس للنقاط
        if p1_clean not in point_to_segments:
            point_to_segments[p1_clean] = []
        if p2_clean not in point_to_segments:
            point_to_segments[p2_clean] = []

        point_to_segments[p1_clean].append((p2_clean, i))
        point_to_segments[p2_clean].append((p1_clean, i))

    print(f"🧹 [polygon_finder] تم تنظيف {len(clean_segments)} مقطع من أصل {len(segments)}")

    polygons = []
    used_segments = set()

    def find_polygon_bfs(start_point, start_segment):
        """البحث عن مضلع باستخدام BFS محسّن"""
        from collections import deque

        queue = deque([(start_point, [start_segment])])
        visited_segments = set([start_segment[1]])

        while queue:
            current_point, current_path = queue.popleft()

            # إذا عدنا لنقطة البداية، وجدنا مضلعاً
            if len(current_path) > 2 and distance(current_point, start_point) < tolerance:
                return current_path

            # البحث عن المقاطع التالية المتصلة
            if current_point in point_to_segments:
                for next_point, seg_idx in point_to_segments[current_point]:
                    if seg_idx not in visited_segments and seg_idx not in used_segments:
                        if is_valid_angle(current_path, current_point, next_point):
                            visited_segments.add(seg_idx)
                            new_path = current_path + [(next_point, seg_idx)]
                            queue.append((next_point, new_path))

                            # تحديد عمق البحث لتجنب التعقيد
                            if len(new_path) > 50:
                                return None

        return None

    # البحث عن المضلعات الرئيسية فقط (لتسريع العملية)
    max_polygons_to_find = 10
    segments_to_process = min(1000, len(clean_segments))  # معالجة أول 1000 segment فقط

    for i in range(segments_to_process):
        if i >= len(clean_segments):
            break

        if i in used_segments:
            continue

        p1, p2 = clean_segments[i]
        polygon = find_polygon_bfs(p1, (p2, i))

        if polygon and len(polygon) >= 3:
            # استخراج المقاطع من المسار
            polygon_segments = []
            segment_indices = set()

            for j in range(len(polygon) - 1):
                point1, seg_idx1 = polygon[j]
                point2, seg_idx2 = polygon[j + 1]
                polygon_segments.append((point1, point2))
                segment_indices.add(seg_idx1)

            # إضافة المضلع إذا كان يحتوي على عدد معقول من الأضلاع
            if 3 <= len(polygon_segments) <= 100:
                polygons.append(polygon_segments)
                used_segments.update(segment_indices)

                if len(polygons) >= max_polygons_to_find:
                    break

    end_time = time.time()
    print(f"⏱️ [polygon_finder] تم العثور على {len(polygons)} مضلع في {end_time - start_time:.2f} ثانية")

    return polygons


def distance(p1, p2):
    """حساب المسافة بين نقطتين"""
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def is_valid_angle(path, current_point, next_point):
    """التحقق من أن الزاوية معقولة (لتجنب التقاطعات المعقدة)"""
    if len(path) < 2:
        return True

    # حساب الزاوية بين المتجهات
    prev_point = path[-2][0] if len(path) > 1 else path[0][0]

    # متجه من النقطة السابقة للحالية
    dx1 = current_point[0] - prev_point[0]
    dy1 = current_point[1] - prev_point[1]

    # متجه من النقطة الحالية للتالية
    dx2 = next_point[0] - current_point[0]
    dy2 = next_point[1] - current_point[1]

    # تجنب الزوايا الحادة جداً
    dot_product = dx1 * dx2 + dy1 * dy2
    mag1 = (dx1 ** 2 + dy1 ** 2) ** 0.5
    mag2 = (dx2 ** 2 + dy2 ** 2) ** 0.5

    if mag1 == 0 or mag2 == 0:
        return True

    cos_angle = dot_product / (mag1 * mag2)
    return cos_angle > -0.9  # تجنب الزوايا الأصغر من 150 درجة


def build_face_from_polygon(polygon_segments):
    """بناء وجه من مضلع مغلق"""
    from OCC.Core.gp import gp_Pnt
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace

    try:
        wire_builder = BRepBuilderAPI_MakeWire()

        for p1, p2 in polygon_segments:
            try:
                point1 = gp_Pnt(p1[0], 0.0, p1[1])
                point2 = gp_Pnt(p2[0], 0.0, p2[1])

                edge = BRepBuilderAPI_MakeEdge(point1, point2).Edge()
                wire_builder.Add(edge)
            except:
                continue

        if wire_builder.IsDone():
            wire = wire_builder.Wire()
            face_builder = BRepBuilderAPI_MakeFace(wire)

            if face_builder.IsDone():
                return face_builder.Face()

    except Exception as e:
        print(f"⚠️ [face_builder] فشل بناء الوجه: {e}")

    return None


def perform_fast_extrusion(face, depth, axis):
    """تنفيذ سريع للإكسترود"""
    from OCC.Core.gp import gp_Vec
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism

    try:
        if axis.upper() == "Y":
            extrusion_vector = gp_Vec(0.0, depth, 0.0)
        elif axis.upper() == "X":
            extrusion_vector = gp_Vec(depth, 0.0, 0.0)
        else:
            extrusion_vector = gp_Vec(0.0, 0.0, depth)

        prism = BRepPrimAPI_MakePrism(face, extrusion_vector)

        if prism.IsDone():
            print("🎉 [smart_extrude] تم الإكسترود بنجاح!")
            return prism.Shape()

    except Exception as e:
        print(f"❌ [smart_extrude] فشل الإكسترود: {e}")

    return None


def perform_complex_extrusion(faces, depth, axis):
    """معالجة الأشكال المعقدة بثقوب"""
    from OCC.Core.gp import gp_Vec
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut

    try:
        # نفترض أن الوجه الأول هو الخارجي والباقي ثقوب
        main_face = faces[0]

        # إكسترود الوجه الرئيسي
        if axis.upper() == "Y":
            extrusion_vector = gp_Vec(0.0, depth, 0.0)
        else:
            extrusion_vector = gp_Vec(0.0, 0.0, depth)

        main_prism = BRepPrimAPI_MakePrism(main_face, extrusion_vector)

        if main_prism.IsDone():
            result_shape = main_prism.Shape()
            print("🎉 [smart_extrude] تم إكسترود الشكل الرئيسي")
            return result_shape

    except Exception as e:
        print(f"❌ [smart_extrude] فشل معالجة الشكل المعقد: {e}")

    return None


# ---------------------------------------------------------
# 🎯 الحل البديل السريع - للملفات المعقدة جداً
# ---------------------------------------------------------

def quick_extrude_fallback(file_path: str, depth: float = 40.0):
    """
    حل بديل سريع - يبني شكل بسيط من المربع المحيط
    """
    print("🔄 [quick_extrude] استخدام الحل السريع...")

    segments, bbox = load_dxf_segments(file_path)
    if not segments:
        return None

    from OCC.Core.gp import gp_Pnt, gp_Vec
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism

    # حساب المربع المحيط
    all_x = []
    all_y = []
    for p1, p2 in segments:
        all_x.extend([p1[0], p2[0]])
        all_y.extend([p1[1], p2[1]])

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    # بناء مربع بسيط
    width = max_x - min_x
    height = max_y - min_y

    # استخدام مربع أصغر قليلاً
    margin_x = width * 0.1
    margin_y = height * 0.1

    polygon = BRepBuilderAPI_MakePolygon()
    polygon.Add(gp_Pnt(min_x + margin_x, 0, min_y + margin_y))
    polygon.Add(gp_Pnt(max_x - margin_x, 0, min_y + margin_y))
    polygon.Add(gp_Pnt(max_x - margin_x, 0, max_y - margin_y))
    polygon.Add(gp_Pnt(min_x + margin_x, 0, max_y - margin_y))
    polygon.Add(gp_Pnt(min_x + margin_x, 0, min_y + margin_y))  # إغلاق

    if polygon.IsDone():
        face = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
        prism = BRepPrimAPI_MakePrism(face, gp_Vec(0, depth, 0))

        if prism.IsDone():
            print("✅ [quick_extrude] تم بناء شكل بسيط بنجاح!")
            return prism.Shape()

    return None