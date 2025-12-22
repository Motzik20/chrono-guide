"use client";

import { useRef, useState } from "react";
import {
  Form,
  FormItem,
  FormLabel,
  FormControl,
  FormField,
} from "@/components/ui/form";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiRequest } from "@/lib/chrono-client";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FileText, Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const ACCEPTED_FILE_TYPES = ["image/jpeg", "image/png", "application/pdf"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const fileSchema = z.object({
  file: z
    .instanceof(File, { message: "Please select a valid file" })
    .refine((file) => file.size <= MAX_FILE_SIZE, "File must be less than 10MB")
    .refine(
      (file) => ACCEPTED_FILE_TYPES.includes(file.type),
      "Only JPG, PNG, and PDF files are allowed"
    ),
});

const textSchema = z.object({
  text: z
    .string()
    .min(1, "Text is required")
    .max(10000, "Text must be less than 10000 characters"),
});

const taskDraft = z.object({
  title: z.string(),
  description: z.string(),
  expected_duration_minutes: z.number().min(1).max(480),
  tips: z.array(z.string()).min(2).max(4),
});

const taskDrafts = z.array(taskDraft);

export default function IngestionInput() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"file" | "text">("file");
  const fileInputRef = useRef<HTMLInputElement>(null);
  async function onFileSubmit(values: z.infer<typeof fileSchema>) {
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", values.file);
      const response: z.infer<typeof taskDrafts> = await apiRequest(
        "/tasks/ingest/file",
        taskDrafts,
        {
          method: "POST",
          body: formData,
        }
      );
      console.log("File ingestion response:", response);
    } catch (error) {
      console.error("File ingestion failed:", error);
    }
  }
  function onTextSubmit(values: z.infer<typeof textSchema>) {
    console.log(values);
  }
  const handleBrowseFiles = () => {
    fileInputRef.current?.click();
  };
  const fileForm = useForm<z.infer<typeof fileSchema>>({
    resolver: zodResolver(fileSchema),
  });

  const textForm = useForm<z.infer<typeof textSchema>>({
    resolver: zodResolver(textSchema),
    defaultValues: {
      text: "",
    },
  });

  const handleFileChange = (file: File | null) => {
    setSelectedFile(file);
    fileForm.setValue("file", file as File);
    if (!file) {
      fileInputRef.current!.value = "";
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && ACCEPTED_FILE_TYPES.includes(file.type)) {
      handleFileChange(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <Tabs
      value={activeTab}
      onValueChange={(v) => setActiveTab(v as "file" | "text")}
    >
      <TabsList>
        <TabsTrigger value="file">
          <Upload className="mr-2 w-4 h-4" />
          Upload File
        </TabsTrigger>
        <TabsTrigger value="text">
          <FileText className="mr-2 w-4 h-4" />
          Enter Text
        </TabsTrigger>
      </TabsList>
      <TabsContent value="file" className="mt-4">
        <Form {...fileForm}>
          <form
            onSubmit={fileForm.handleSubmit(onFileSubmit)}
            className="space-y-4"
          >
            <FormField
              control={fileForm.control}
              name="file"
              render={({ field: { value, onChange, ...fieldProps } }) => (
                <FormItem>
                  <FormLabel>Ingestion Input</FormLabel>
                  <FormControl>
                    <div
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      onClick={handleBrowseFiles}
                      className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer"
                    >
                      {selectedFile ? (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <FileText className="h-5 w-5" />
                            <span className="text-sm">{selectedFile.name}</span>
                            <span className="text-xs text-muted-foreground">
                              ({(selectedFile.size / 1024).toFixed(1)} KB)
                            </span>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              handleFileChange(null);
                              fileForm.reset();
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ) : (
                        <div>
                          <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                          <p className="text-sm text-muted-foreground mb-2">
                            Drag and drop a file here, or click to browse
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Supported: JPEG, PNG, PDF (max 10MB)
                          </p>
                        </div>
                      )}
                      <Input
                        {...fieldProps}
                        ref={fileInputRef}
                        type="file"
                        accept={ACCEPTED_FILE_TYPES.join(",")}
                        className="hidden"
                        id="file-input"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleFileChange(file);
                        }}
                      />
                      <label htmlFor="file-input" className="cursor-pointer">
                        {!selectedFile && (
                          <Button
                            type="button"
                            variant="outline"
                            className="mt-4"
                          >
                            Browse Files
                          </Button>
                        )}
                      </label>
                    </div>
                  </FormControl>
                </FormItem>
              )}
            />
            <Button type="submit" disabled={!selectedFile}>
              Submit
            </Button>
          </form>
        </Form>
      </TabsContent>
      <TabsContent value="text" className="mt-4">
        <Form {...textForm}>
          <form
            onSubmit={textForm.handleSubmit(onTextSubmit)}
            className="space-y-4"
          >
            <FormField
              control={textForm.control}
              name="text"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Ingestion Input</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="Enter your text here..."
                      className="min-h-[200px]"
                    />
                  </FormControl>
                </FormItem>
              )}
            />
            <Button type="submit" disabled={!textForm.formState.isValid}>
              Submit
            </Button>
          </form>
        </Form>
      </TabsContent>
    </Tabs>
  );
}
