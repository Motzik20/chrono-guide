export const formatDateTime = (dateString: string, userTimezone: string) => {
  const date = new Date(dateString);
  return date.toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: userTimezone,
  });
};

export const formatDuration = (startTime: string, endTime: string) => {
  const start = new Date(startTime);
  const end = new Date(endTime);
  const diffMs = end.getTime() - start.getTime();
  const diffMins = Math.round(diffMs / (1000 * 60));

  if (diffMins < 60) {
    return `${diffMins} min`;
  }
  const hours = Math.floor(diffMins / 60);
  const mins = diffMins % 60;
  return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
};

export const formatFloatingTime = (dateString: string) => {
  const literalTime = dateString.slice(0, 19);

  const date = new Date(literalTime);

  return date.toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  });
};
