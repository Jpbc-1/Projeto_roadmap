import React, { useEffect, useMemo, useRef } from 'react';
import { ScrollView, Text, View, StyleSheet } from 'react-native';
import { colors, spacing, typography } from '../theme/colors';
import { AgendaItem } from '../hooks/useAgenda';
import { isSameDay } from '../utils/dateUtils';
import AgendaEventCard from './AgendaEventCard';

type DayTimelineProps = {
  day: Date;
  items: AgendaItem[];
  onPressItem?: (item: AgendaItem) => void;
};

const START_HOUR = 6;
const END_HOUR = 23;
const HOUR_HEIGHT = 64;
// A point-in-time reminder still needs a tappable, readable card —
// this is the shortest a card ever gets, equivalent to ~35min of a
// timed event.
const MIN_CARD_HEIGHT = 38;
const LABEL_COLUMN_WIDTH = 52;

function minutesFromStart(date: Date): number {
  return (date.getHours() - START_HOUR) * 60 + date.getMinutes();
}

export default function DayTimeline({ day, items, onPressItem }: DayTimelineProps) {
  const scrollRef = useRef<ScrollView>(null);
  const isToday = isSameDay(day, new Date());
  const hours = useMemo(
    () => Array.from({ length: END_HOUR - START_HOUR + 1 }, (_, i) => START_HOUR + i),
    []
  );
  // +1 so the container reaches past the START of the last hour row (its
  // top offset alone would clip that row out of the scrollable area),
  // plus one row of breathing room at the very bottom.
  const totalHeight = (END_HOUR - START_HOUR + 2) * HOUR_HEIGHT;

  const now = new Date();
  const nowOffset = (minutesFromStart(now) / 60) * HOUR_HEIGHT;
  const showNowLine = isToday && now.getHours() >= START_HOUR && now.getHours() <= END_HOUR;

  // Open roughly at "now" (or the day's first item) instead of always at
  // 06:00 — nobody wants to scroll past six empty hours to see today.
  useEffect(() => {
    const defaultAnchor = new Date(day);
    defaultAnchor.setHours(9, 0, 0, 0);
    const anchorMinutes = showNowLine
      ? minutesFromStart(now)
      : items.length > 0
        ? minutesFromStart(items[0].time)
        : minutesFromStart(defaultAnchor);
    const targetY = Math.max(0, (anchorMinutes / 60) * HOUR_HEIGHT - HOUR_HEIGHT * 1.5);
    // Defer to after layout so the ScrollView has its content height.
    const timeout = setTimeout(() => scrollRef.current?.scrollTo({ y: targetY, animated: false }), 0);
    return () => clearTimeout(timeout);
    // Re-anchor whenever the viewed day changes, not on every item edit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [day]);

  return (
    <ScrollView ref={scrollRef} showsVerticalScrollIndicator={false} style={styles.scroll}>
      <View style={[styles.grid, { height: totalHeight }]}>
        {hours.map((hour, i) => (
          <View key={hour} style={[styles.hourRow, { top: i * HOUR_HEIGHT }]}>
            <Text style={styles.hourLabel}>{String(hour).padStart(2, '0')}:00</Text>
            <View style={styles.hourLine} />
          </View>
        ))}

        {showNowLine && (
          <View style={[styles.nowLine, { top: nowOffset }]}>
            <View style={styles.nowDot} />
            <View style={styles.nowLineBar} />
          </View>
        )}

        {items.map((item) => {
          const top = (minutesFromStart(item.time) / 60) * HOUR_HEIGHT;
          const height =
            item.durationMinutes != null
              ? Math.max((item.durationMinutes / 60) * HOUR_HEIGHT, MIN_CARD_HEIGHT)
              : MIN_CARD_HEIGHT;
          return (
            <View key={item.key} style={[styles.itemSlot, { top, height }]}>
              <AgendaEventCard item={item} onPress={() => onPressItem?.(item)} />
            </View>
          );
        })}
      </View>

      {items.length === 0 && (
        <View style={styles.emptyState} pointerEvents="none">
          <Text style={styles.emptyText}>Nada marcado por aqui — toque em "+" para adicionar algo.</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
  },
  grid: {
    position: 'relative',
  },
  hourRow: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: HOUR_HEIGHT,
    flexDirection: 'row',
  },
  hourLabel: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
    width: LABEL_COLUMN_WIDTH,
    marginTop: -7, // centers the label on the line instead of below it
  },
  hourLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(31,22,12,0.14)',
    marginTop: 0,
  },
  nowLine: {
    position: 'absolute',
    left: LABEL_COLUMN_WIDTH,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    zIndex: 1,
  },
  nowDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.streak,
    marginLeft: -4,
  },
  nowLineBar: {
    flex: 1,
    height: 1.5,
    backgroundColor: colors.streak,
  },
  itemSlot: {
    position: 'absolute',
    left: LABEL_COLUMN_WIDTH + spacing.sm,
    right: spacing.sm,
  },
  emptyState: {
    position: 'absolute',
    top: 0,
    left: LABEL_COLUMN_WIDTH + spacing.md,
    right: spacing.md,
    paddingTop: spacing.xl,
  },
  emptyText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
});
