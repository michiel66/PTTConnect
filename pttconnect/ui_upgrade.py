CHANNEL_TREE_BUILDER_KT = r'''
package com.toosarax.ts3client.client

import com.toosarax.ts3client.protocol.ChannelInfo

object ChannelTreeBuilder {

    fun build(flatChannels: List<ChannelInfo>): List<ChannelTreeNode> {
        if (flatChannels.isEmpty()) return emptyList()

        val byId = flatChannels.associateBy { it.id }
        val channelIds = byId.keys
        val childrenByParent = flatChannels.groupBy { it.parentId }

        fun buildLevel(parentId: Int): List<ChannelTreeNode> {
            val siblings = childrenByParent[parentId].orEmpty()

            return orderSiblings(
                siblings = siblings,
                byId = byId,
            ).map { channel ->
                ChannelTreeNode(
                    channel = channel,
                    children = buildLevel(channel.id),
                )
            }
        }

        val rootParentIds = flatChannels
            .map { it.parentId }
            .filter { it !in channelIds }
            .distinct()

        return rootParentIds.flatMap { parentId ->
            buildLevel(parentId)
        }
    }

    internal fun orderSiblings(
        siblings: List<ChannelInfo>,
        byId: Map<Int, ChannelInfo>,
    ): List<ChannelInfo> {
        if (siblings.size <= 1) return siblings

        val siblingIds = siblings
            .map { it.id }
            .toSet()

        val originalIndex = siblings
            .withIndex()
            .associate { indexed ->
                indexed.value.id to indexed.index
            }

        val followers = siblings.groupBy {
            it.predecessorId
        }

        val visited = mutableSetOf<Int>()
        val ordered = mutableListOf<ChannelInfo>()

        fun walk(start: ChannelInfo) {
            var current: ChannelInfo? = start

            while (
                current != null &&
                visited.add(current.id)
            ) {
                ordered += current

                current = followers[current.id]
                    .orEmpty()
                    .filter { it.id !in visited }
                    .minByOrNull {
                        originalIndex[it.id]
                            ?: Int.MAX_VALUE
                    }
            }
        }

        /*
         * Belangrijk:
         * TeamSpeak channel_order verwijst alleen naar
         * een voorganger binnen dezelfde parent.
         *
         * Daarom controleren we siblingIds en NIET alle
         * kanaal-IDs van de server.
         */
        val heads = siblings
            .filter { channel ->
                channel.predecessorId == 0 ||
                    channel.predecessorId !in siblingIds
            }
            .sortedBy {
                originalIndex[it.id] ?: Int.MAX_VALUE
            }

        heads.forEach(::walk)

        /*
         * Fallback voor kapotte/onvolledige chains.
         * Hiermee verdwijnen kanalen nooit uit de lijst.
         */
        siblings
            .filter { it.id !in visited }
            .sortedBy {
                originalIndex[it.id] ?: Int.MAX_VALUE
            }
            .forEach(::walk)

        return ordered
    }
}
'''
