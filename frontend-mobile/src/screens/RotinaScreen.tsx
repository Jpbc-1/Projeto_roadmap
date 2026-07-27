import React, { useState } from 'react';
import { Text, ScrollView, StyleSheet } from 'react-native';
import { colors, spacing, typography } from '../theme/colors';
import AvailabilityCard from '../components/AvailabilityCard';
import NotificationCard from '../components/NotificationCard';
import MonthHeatmap from '../components/MonthHeatmap';
import WoodBackground from '../components/WoodBackground';

export default function RotinaScreen() {
  const [selectedDays, setSelectedDays] = useState<string[]>(['seg', 'ter', 'qua', 'qui', 'sex']);
  const [selectedPeriod, setSelectedPeriod] = useState('noite');

  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [frequency, setFrequency] = useState('moderadas');
  const [quietHours, setQuietHours] = useState('noite');

  function toggleDay(key: string) {
    setSelectedDays((prev) => (prev.includes(key) ? prev.filter((d) => d !== key) : [...prev, key]));
  }

  return (
    <WoodBackground>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.heading}>Rotina</Text>
        <Text style={styles.subheading}>Como e quando a IA te lembra das suas missões</Text>

        <AvailabilityCard
          selectedDays={selectedDays}
          onToggleDay={toggleDay}
          selectedPeriod={selectedPeriod}
          onSelectPeriod={setSelectedPeriod}
        />

        <NotificationCard
          enabled={notificationsEnabled}
          onToggleEnabled={setNotificationsEnabled}
          frequency={frequency}
          onSelectFrequency={setFrequency}
          quietHours={quietHours}
          onSelectQuietHours={setQuietHours}
        />

        {/* Sample data — swap for real completion history */}
        <MonthHeatmap activeDays={[1, 2, 3, 5, 6, 8, 9, 10, 11, 12, 15, 16, 17, 19, 20]} />
      </ScrollView>
    </WoodBackground>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  heading: {
    ...typography.screenTitle,
    color: colors.textPrimary,
  },
  subheading: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
});
