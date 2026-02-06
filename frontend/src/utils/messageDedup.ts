/**
 * Message Deduplication Utility
 * Intelligently merges incoming messages with existing ones
 */

export interface DeduplicatableMessage {
    id: string;
    role: string;
    content: string;
    created_at?: string;
    isOptimistic?: boolean;
}

/**
 * Merges incoming messages with existing messages using intelligent deduplication
 * 
 * Strategy:
 * 1. Exact ID match → Update existing message
 * 2. Optimistic match (content + role match with temp ID) → Replace optimistic with real
 * 3. No match → Add as new message
 * 
 * @param existingMessages Current messages in state
 * @param incomingMessages New messages from API
 * @returns Deduplicated and sorted message array
 */
export function deduplicateMessages<T extends DeduplicatableMessage>(
    existingMessages: T[],
    incomingMessages: T[]
): T[] {
    // Create a Map for O(1) lookup
    const messagesMap = new Map<string, T>();

    // Step 1: Add all existing messages to map
    existingMessages.forEach((msg) => {
        messagesMap.set(msg.id, msg);
    });

    // Step 2: Process incoming messages
    incomingMessages.forEach((incomingMsg) => {
        // Check for exact ID match
        if (messagesMap.has(incomingMsg.id)) {
            // Update existing message with fresh data
            messagesMap.set(incomingMsg.id, incomingMsg);
            return;
        }

        // Check for optimistic match (temp message that should be replaced)
        // We look for a temp message with the same role and similar content
        const optimisticMatch = Array.from(messagesMap.values()).find((existingMsg) => {
            if (!existingMsg.id) return false;
            const isTemp = existingMsg.id.startsWith('temp-') || existingMsg.isOptimistic === true;
            if (!isTemp) return false;

            if (existingMsg.role !== incomingMsg.role) return false;

            // Normalize content for comparison (trim whitespace, handle potential line ending diffs)
            const cleanExisting = existingMsg.content.trim();
            const cleanIncoming = incomingMsg.content.trim();

            return cleanExisting === cleanIncoming;
        });

        if (optimisticMatch) {
            // Remove the temp message
            messagesMap.delete(optimisticMatch.id);
            // Add the real message
            messagesMap.set(incomingMsg.id, incomingMsg);
        } else {
            // No match found - add as new message
            messagesMap.set(incomingMsg.id, incomingMsg);
        }
    });

    // Step 3: Convert back to array and sort by created_at
    const dedupedMessages = Array.from(messagesMap.values());

    dedupedMessages.sort((a, b) => {
        const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
        // Handle NaN
        const valA = isNaN(timeA) ? 0 : timeA;
        const valB = isNaN(timeB) ? 0 : timeB;
        return valA - valB;
    });

    return dedupedMessages;
}

/**
 * Helper: Mark a message as optimistic (for UI purposes)
 */
export function markAsOptimistic<T extends DeduplicatableMessage>(message: T): T {
    return {
        ...message,
        isOptimistic: true,
    };
}
