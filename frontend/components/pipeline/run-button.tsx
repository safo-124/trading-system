"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export function RunButton() {
  return (
    <Button onClick={() => window.location.reload()} type="button">
      <RefreshCw />
      Refresh Data
    </Button>
  );
}
