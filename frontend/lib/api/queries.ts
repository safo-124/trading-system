"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getLatestPredictions,
  type LatestPredictionsResponse,
  type PipelineRunResponse,
  runPipeline,
} from "@/lib/api/client";

export const queryKeys = {
  latestPredictions: ["predictions", "latest"] as const,
};

export function useLatestPredictionsQuery(initialData?: LatestPredictionsResponse) {
  return useQuery({
    queryKey: queryKeys.latestPredictions,
    queryFn: getLatestPredictions,
    initialData,
  });
}

export function useRunPipelineMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: runPipeline,
    onSuccess: (data: PipelineRunResponse) => {
      queryClient.setQueryData<LatestPredictionsResponse>(queryKeys.latestPredictions, {
        predictions: data.picks,
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.latestPredictions });
    },
  });
}
