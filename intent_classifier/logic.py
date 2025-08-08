import asyncio
import logging

from .conf import conf, processors

logger = logging.getLogger(conf.APP_NAME)


# --------------------------------------------------------------------------- #
# Layer logic
# --------------------------------------------------------------------------- #
async def classify_segment(
    task,
    previous_segments: list[str],
    segment: str,
    layers: list[dict],
    running_cost: int = 0,
    is_partial: bool = False,
) -> tuple[int, dict] | None:
    
    for layer in layers:
        layer_instance = layer["instance"]
        if layer.get("cost", 0) + running_cost > task.job_budget or not await layer_instance.check_condition(
            previous_segments, segment, is_partial=is_partial):
            continue

        result = await layer_instance.classify(
            previous_segments, segment, is_partial=is_partial
        )
        running_cost += layer.get("cost", 0)
        await layer_instance.on_complete(result)

        threshold = float(
            layer.get("confidence_threshold", processors.DEFAULT_INTENT_CONFIDENCE_THRESHOLD)
        )
        result_confidence = result.get("confidence", 0.5)

        if result_confidence > threshold:
            await layer_instance.on_success(result)
            return running_cost, result
        else:
            await layer_instance.on_failure(result, "Result below confidence threshold")
    return running_cost, None



async def segment_text(intent_separators: list, content: str) -> list[str]:
    for intent_separator in intent_separators:
        separator_instance = intent_separator["instance"]
        
        logger.debug("Checking intent separator: %s", intent_separator["alias"])
        if await separator_instance.check_condition(content):
            logger.debug("Intent separator %s matched condition", intent_separator["alias"])
            segments = await separator_instance.create_segments(content)
            logger.debug("Segments created: %r", segments)

            if (segments is not None and len(segments) > 0 and
                all(await asyncio.gather(*[separator_instance.validate_segment(seg) for seg in segments]))):
                logger.debug("Using segments from separator: %s", intent_separator["alias"])
                return segments
        
    logger.debug("No intent separators matched; using original content as single segment.")
    return [content]  # Default to single segment if no separators
