/**
 * This file contains the JSX code for the delete button to be added to each face card
 *
 * Step 2: Find the JSX element where faces are rendered
 * Look for code that matches this pattern (the structure may vary slightly):
 * 
 * <div className="relative aspect-square w-full overflow-hidden rounded-md bg-muted">
 *   <img 
 *     alt="Detected face" 
 *     data-ai-hint="person face" 
 *     loading="lazy" 
 *     decoding="async" 
 *     data-nimg="fill" 
 *     className="object-cover" 
 *     ... // other image props
 *   />
 *   {/* ADD THE BUTTON HERE, just before the closing div */}
 * </div>
 */

// Delete button JSX to add inside the face card div
// Add this right after the <img> tag but before the closing </div>

<button
  className="absolute top-1 right-1 h-6 w-6 rounded-full bg-black/50 p-1 text-white hover:bg-red-500/70 transition-colors"
  onClick={(e) => handleRemoveFace(e, face.id)}
  title="Remove face"
>
  <Trash2 className="h-4 w-4" />
</button>

// If you prefer a simpler version without importing Trash2 icon
<button
  className="absolute top-1 right-1 h-6 w-6 rounded-full bg-black/50 p-1 text-white hover:bg-red-500/70 transition-colors"
  onClick={(e) => handleRemoveFace(e, face.id)}
  title="Remove face"
>
  ✕
</button>