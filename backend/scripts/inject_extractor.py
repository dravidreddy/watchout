import os

file_path = "c:/Users/dravi/OneDrive/Desktop/Watchout/backend/app/api/routes/chat.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import_target = "from app.prompts import build_trip_title_prompt"
if import_target in content and "MemoryExtractorAgent" not in content:
    content = content.replace(import_target, import_target + "\nfrom app.agents.memory_extractor import MemoryExtractorAgent")

# Find the exact try/except block where we save the turn
old_block = """                    await db.trips.update_one(
                        {"trip_id": trip_id, "user_id": uid},
                        {"$set": fields},
                    )
                except Exception as exc:"""

new_block = """                    await db.trips.update_one(
                        {"trip_id": trip_id, "user_id": uid},
                        {"$set": fields},
                    )
                    
                    # ---- Extract Long-Term Memory ----
                    if assistant_msg:
                        try:
                            extractor = MemoryExtractorAgent()
                            turn_history = history[-10:] + [{"role": "user", "content": chat_request.message}, {"role": "assistant", "content": assistant_msg}]
                            await extractor.extract_and_store(
                                user_id=uid,
                                recent_history=turn_history,
                                current_preferences=fields.get("preferences", {})
                            )
                        except Exception as extractor_exc:
                            logger.error(f"Background memory extraction failed: {extractor_exc}")

                except Exception as exc:"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Injected memory extractor into chat.py")
else:
    print("FAILED: Could not find target block in chat.py")
