extends RefCounted
## Shared camera rule: set the playable footprint in each level's design units.
## The default framing is always 1.0, independent of resolution or browser DPR.
const REFERENCE_AREA := 1080.0*675.0
const REFERENCE_MAX_ZOOM := 1.85

static func zoom_cap_for(footprint: Vector2) -> float:
	var area:=maxf(1.0,footprint.x*footprint.y)
	return clampf(REFERENCE_MAX_ZOOM*sqrt(area/REFERENCE_AREA),1.35,3.2)
