"use client";

import { Separator } from "@/components/ui/separator";

interface TasksSplitViewProps {
  leftContent: React.ReactNode;
  rightContent: React.ReactNode;
}

export default function TasksSplitView({
  leftContent,
  rightContent,
}: TasksSplitViewProps) {
  return (
    <div className="flex w-full h-full flex-row">
      <div className="w-1/2 flex justify-center items-center p-4">
        {leftContent}
      </div>
      <Separator orientation="vertical" className="" />
      <div className="w-1/2 flex justify-center items-center p-4">
        {rightContent}
      </div>
    </div>
  );
}
