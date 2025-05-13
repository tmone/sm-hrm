'use client';

import React from 'react';
import { Trash2 } from 'lucide-react';

interface DeleteFaceButtonProps {
  faceId: string;
  onDelete: (e: React.MouseEvent, faceId: string) => void;
}

/**
 * Delete Face Button Component
 * Add this component inside your face card div, just after the Image component
 * 
 * Example usage in the face card:
 * 
 * <div className="relative aspect-square w-full overflow-hidden rounded-md bg-muted">
 *   <Image ... />
 *   <DeleteFaceButton faceId={face.id} onDelete={handleRemoveFace} />
 *   {/* other face card content */}
 * </div>
 */
export default function DeleteFaceButton({ faceId, onDelete }: DeleteFaceButtonProps) {
  return (
    <button
      className="absolute top-1 right-1 h-6 w-6 rounded-full bg-black/50 p-1 text-white hover:bg-red-500/70 transition-colors z-10"
      onClick={(e) => onDelete(e, faceId)}
      title="Remove face"
    >
      <Trash2 className="h-4 w-4" />
    </button>
  );
}