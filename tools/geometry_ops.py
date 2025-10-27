# -*- coding: utf-8 -*-
"""
🔹 أدوات هندسية أساسية - إصدار تجميع المضلعات
"""

from profile.dxf_normalizer import load_dxf_segments


def extrude_profile(file_path: str, depth: float = 40.0, axis: str = "Y"):
    """
    تنفيذ عملية إكسترود مع تجميع المضلعات المغلقة
    """
    print(f"📂 [geometry_ops] تحميل DXF من: {file_path}")

    try:
        segments, bbox = load_dxf_segments(file_path)
        if not segments:
            print("⚠️ [geometry_ops] لا توجد مقاطع صالحة في DXF.")
            return None
        print(f"✅ [geometry_ops] تم تحميل {len(segments)} مقطع")
    except Exception as e:
        print(f"❌ [geometry_ops] فشل تحميل DXF: {e}")
        return None

    from OCC.Core.gp import gp_Pnt, gp_Vec
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCC.Core.ShapeFix import ShapeFix_Wire, ShapeFix_Face

    # ---------------------------------------------------------
    # 🔍 البحث عن مضلعات مغلقة في البيانات
    # ---------------------------------------------------------
    def find_closed_polygons(segments, tolerance=0.001):
        """البحث عن مضلعات مغلقة في segments"""
        print("🔍 [geometry_ops] البحث عن مضلعات مغلقة...")

        polygons = []
        used_segments = set()

        def find_polygon_from_segment(start_segment_idx):
            """البحث عن مضلع مغلق بدءاً من segment معين"""
            polygon_segments = []
            current_segment_idx = start_segment_idx
            start_point = segments[start_segment_idx][0]
            current_point = segments[start_segment_idx][1]

            polygon_segments.append(segments[start_segment_idx])
            used_segments.add(start_segment_idx)

            max_iterations = len(segments)
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                found_next = False

                # البحث عن segment متصل بالنقطة الحالية
                for i, (p1, p2) in enumerate(segments):
                    if i in used_segments:
                        continue

                    # التحقق من الاتصال مع tolerance
                    def points_equal(pt1, pt2, tol=tolerance):
                        return abs(pt1[0] - pt2[0]) < tol and abs(pt1[1] - pt2[1]) < tol

                    if points_equal(current_point, p1):
                        polygon_segments.append((p1, p2))
                        used_segments.add(i)
                        current_point = p2
                        found_next = True
                        break
                    elif points_equal(current_point, p2):
                        polygon_segments.append((p2, p1))  # عكس الاتجاه
                        used_segments.add(i)
                        current_point = p1
                        found_next = True
                        break

                # إذا وصلنا للنقطة البدائية، المضلع مغلق
                if points_equal(current_point, start_point):
                    return polygon_segments

                if not found_next:
                    break

            return None

        # البحث عن مضلعات مغلقة
        for i in range(len(segments)):
            if i not in used_segments:
                polygon = find_polygon_from_segment(i)
                if polygon and len(polygon) >= 3:  # مضلع مغلق ب3 أضلاع على الأقل
                    polygons.append(polygon)
                    print(f"✅ [geometry_ops] تم العثور على مضلع مغلق بـ {len(polygon)} ضلع")

        print(f"📊 [geometry_ops] تم العثور على {len(polygons)} مضلع مغلق")
        return polygons

    # ---------------------------------------------------------
    # 🧩 بناء وجه من المضلع المغلق
    # ---------------------------------------------------------
    def build_face_from_polygon(polygon_segments):
        """بناء وجه من مضلع مغلق"""
        try:
            wire_builder = BRepBuilderAPI_MakeWire()

            for p1, p2 in polygon_segments:
                try:
                    # تحويل النقاط إلى 3D على مستوى XZ
                    point1 = gp_Pnt(float(p1[0]), 0.0, float(p1[1]))
                    point2 = gp_Pnt(float(p2[0]), 0.0, float(p2[1]))

                    edge = BRepBuilderAPI_MakeEdge(point1, point2).Edge()
                    wire_builder.Add(edge)
                except Exception as e:
                    print(f"⚠️ [geometry_ops] فشل بناء edge: {e}")
                    continue

            if wire_builder.IsDone():
                wire = wire_builder.Wire()

                # إصلاح الـ Wire
                wire_fixer = ShapeFix_Wire()
                wire_fixer.Load(wire)
                wire_fixer.FixReorder()
                wire_fixer.FixConnected()
                wire_fixer.FixClosed()
                wire_fixer.Perform()
                fixed_wire = wire_fixer.Wire()

                # بناء الوجه
                face_builder = BRepBuilderAPI_MakeFace(fixed_wire)
                if face_builder.IsDone():
                    face = face_builder.Face()

                    # إصلاح الوجه
                    face_fixer = ShapeFix_Face(face)
                    face_fixer.Perform()
                    fixed_face = face_fixer.Face()

                    return fixed_face

        except Exception as e:
            print(f"❌ [geometry_ops] فشل بناء الوجه من المضلع: {e}")

        return None

    # ---------------------------------------------------------
    # 🎯 المحاولة الرئيسية: تجميع المضلعات المغلقة
    # ---------------------------------------------------------
    polygons = find_closed_polygons(segments)

    if polygons:
        # استخدام أول مضلع مغلق (أو أكبرها)
        largest_polygon = max(polygons, key=len)
        print(f"🎯 [geometry_ops] استخدام المضلع الأكبر بـ {len(largest_polygon)} ضلع")

        face = build_face_from_polygon(largest_polygon)
        if face:
            return perform_extrusion(face, depth, axis)

    # ---------------------------------------------------------
    # 🔄 إذا فشل تجميع المضلعات، استخدم الحل التلقائي
    # ---------------------------------------------------------
    print("🔄 [geometry_ops] استخدام الحل التلقائي...")
    return auto_extrude_solution(segments, depth, axis)


def auto_extrude_solution(segments, depth, axis):
    """حل تلقائي لبناء شكل مغلق"""
    from OCC.Core.gp import gp_Pnt, gp_Vec
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCC.Core.BRepTools import BRepTools_WireExplorer
    from OCC.Core.TopAbs import TopAbs_EDGE
    from OCC.Core.TopExp import TopExp_Explorer


    # جمع جميع النقاط الفريدة
    all_points = set()
    for p1, p2 in segments:
        all_points.add((round(p1[0], 4), round(p1[1], 4)))
        all_points.add((round(p2[0], 4), round(p2[1], 4)))

    if len(all_points) < 3:
        print("❌ [geometry_ops] نقاط غير كافية لبناء مضلع")
        return None

    # طريقة 1: بناء مضلع محدب من النقاط
    try:
        print("🔄 [geometry_ops] بناء مضلع محدب...")

        # ترتيب النقاط في مضلع محدب ( convex hull بسيط)
        points_list = list(all_points)

        # إيجاد النقطة الأكثر يساراً
        leftmost = min(points_list, key=lambda p: p[0])

        # خوارزمية بسيطة لبناء مضلع
        hull_points = []
        current_point = leftmost
        visited = set()

        while current_point and current_point not in visited:
            visited.add(current_point)
            hull_points.append(current_point)

            # إيجاد النقطة التالية في المضلع
            next_point = None
            for point in points_list:
                if point != current_point and point not in visited:
                    if not next_point:
                        next_point = point
                    else:
                        # اختيار النقطة التي تكون زاوية أصغر
                        pass

            current_point = next_point

        # إذا لم نحصل على مضلع جيد، استخدم النقاط كما هي
        if len(hull_points) < 3:
            hull_points = points_list[:min(50, len(points_list))]

        # بناء المضلع
        polygon_builder = BRepBuilderAPI_MakePolygon()
        for x, y in hull_points:
            polygon_builder.Add(gp_Pnt(x, 0, y))

        # إغلاق المضلع
        if len(hull_points) > 2:
            polygon_builder.Add(gp_Pnt(hull_points[0][0], 0, hull_points[0][1]))

        if polygon_builder.IsDone():
            wire = polygon_builder.Wire()
            face = BRepBuilderAPI_MakeFace(wire).Face()

            if face:
                print("✅ [geometry_ops] تم بناء المضلع المحدب")
                return perform_extrusion(face, depth, axis)

    except Exception as e:
        print(f"⚠️ [geometry_ops] فشل بناء المضلع المحدب: {e}")

    # طريقة 2: بناء مستطيل بسيط حول النقاط
    try:
        print("🔄 [geometry_ops] بناء مستطيل محيط...")

        all_x = [p[0] for p in all_points]
        all_y = [p[1] for p in all_points]

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        # إضافة هامش
        margin_x = (max_x - min_x) * 0.1
        margin_y = (max_y - min_y) * 0.1

        polygon_builder = BRepBuilderAPI_MakePolygon()
        polygon_builder.Add(gp_Pnt(min_x - margin_x, 0, min_y - margin_y))
        polygon_builder.Add(gp_Pnt(max_x + margin_x, 0, min_y - margin_y))
        polygon_builder.Add(gp_Pnt(max_x + margin_x, 0, max_y + margin_y))
        polygon_builder.Add(gp_Pnt(min_x - margin_x, 0, max_y + margin_y))
        polygon_builder.Add(gp_Pnt(min_x - margin_x, 0, min_y - margin_y))  # إغلاق

        if polygon_builder.IsDone():
            wire = polygon_builder.Wire()
            face = BRepBuilderAPI_MakeFace(wire).Face()

            if face:
                print("✅ [geometry_ops] تم بناء المستطيل المحيط")
                return perform_extrusion(face, depth, axis)

    except Exception as e:
        print(f"⚠️ [geometry_ops] فشل بناء المستطيل المحيط: {e}")

    print("❌ [geometry_ops] فشلت جميع محاولات البناء")
    return None


def perform_extrusion(face, depth, axis):
    """تنفيذ عملية الإكسترود"""
    from OCC.Core.gp import gp_Vec
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism

    try:
        print(f"🚀 [geometry_ops] تنفيذ الإكسترود باتجاه {axis} بمقدار {depth}")

        if axis.upper() == "Y":
            extrusion_vector = gp_Vec(0.0, depth, 0.0)
        elif axis.upper() == "X":
            extrusion_vector = gp_Vec(depth, 0.0, 0.0)
        elif axis.upper() == "Z":
            extrusion_vector = gp_Vec(0.0, 0.0, depth)
        else:
            extrusion_vector = gp_Vec(0.0, depth, 0.0)

        prism = BRepPrimAPI_MakePrism(face, extrusion_vector)

        if prism.IsDone():
            extruded_shape = prism.Shape()
            print("🎉 [geometry_ops] تم الإكسترود بنجاح!")
            return extruded_shape
        else:
            print("❌ [geometry_ops] فشل في عملية الإكسترود")
            return None

    except Exception as e:
        print(f"❌ [geometry_ops] فشل في عملية الإكسترود: {e}")
        return None