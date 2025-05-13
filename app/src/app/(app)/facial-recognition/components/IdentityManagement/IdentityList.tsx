import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Users, User, Tag } from 'lucide-react';
import { IdentityGroup } from '../../types';
import { formatDate } from '../../utils';

interface IdentityListProps {
  identities: IdentityGroup[];
  selectedIdentity: string | null;
  isSelectionMode: boolean;
  onSelectIdentity: (id: string) => void;
  isIdentitySelectionMode?: boolean;
  selectedIdentities?: Record<string, boolean>;
}

export default function IdentityList({
  identities,
  selectedIdentity,
  isSelectionMode,
  onSelectIdentity,
  isIdentitySelectionMode = false,
  selectedIdentities = {}
}: IdentityListProps) {
  if (identities.length === 0) {
    return (
      <div className="text-center py-10 text-muted-foreground">
        No identity groups found.
      </div>
    );
  }
  
  const handleIdentityClick = (id: string) => {
    // Always call onSelectIdentity, regardless of mode
    onSelectIdentity(id);
  };
  
  return (
    <div className="rounded-md border">
      <div className="relative w-full overflow-auto">
        <table className="w-full caption-bottom text-sm">
          <thead className="[&_tr]:border-b">
            <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Identity</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Faces</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Created</th>
            </tr>
          </thead>
          <tbody className="[&_tr:last-child]:border-0">
            {identities.map(identity => (
              <tr 
                key={identity.id} 
                className={`border-b transition-colors hover:bg-muted/50 cursor-pointer ${
                  selectedIdentity === identity.id ? 'bg-primary/10' : ''
                } ${
                  isIdentitySelectionMode && selectedIdentities[identity.id] ? 'bg-primary/10' : ''
                }`}
                onClick={() => handleIdentityClick(identity.id)}
              >
                <td className="p-4 align-middle">
                  <div className="flex items-center gap-3">
                    {isIdentitySelectionMode && (
                      <input 
                        type="checkbox" 
                        className="h-4 w-4" 
                        checked={selectedIdentities[identity.id] || false}
                        onChange={() => onSelectIdentity(identity.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    )}
                    <div className="rounded-full bg-primary/10 p-2">
                      {identity.employee_id ? (
                        <User className="h-4 w-4 text-primary" />
                      ) : (
                        <Tag className="h-4 w-4 text-primary" />
                      )}
                    </div>
                    <div>
                      <div className="font-medium">
                        {identity.name || identity.id}
                      </div>
                      {identity.name && (
                        <div className="text-xs text-muted-foreground">
                          {identity.id}
                        </div>
                      )}
                      {!isSelectionMode && (
                        <div className="text-xs text-blue-600 hover:underline mt-1">
                          Click to view faces
                        </div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="p-4 align-middle">
                  <Badge variant="outline">
                    {identity.face_ids.length} faces
                  </Badge>
                </td>
                <td className="p-4 align-middle">
                  {formatDate(identity.created)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}