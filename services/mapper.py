def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)

    box1_area = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
    box2_area = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])

    union_area = box1_area + box2_area - inter_area

    if union_area == 0:
        return 0

    return inter_area / union_area


def map_damage_to_parts(parts, damages):
    mapped_results = []

    for damage in damages:
        best_part = None
        best_iou = 0

        for part in parts:
            iou = calculate_iou(damage["box"], part["box"])
            if iou > best_iou:
                best_iou = iou
                best_part = part["label"]

        if best_part:
            mapped_results.append(f'{damage["label"]} on {best_part}')
        else:
            mapped_results.append(f'{damage["label"]} detected')

    return mapped_results