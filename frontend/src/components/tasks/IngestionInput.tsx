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
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { useJobManager } from "@/context/job-context";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FileText, Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "sonner";

const ACCEPTED_FILE_TYPES = ["image/jpeg", "image/png", "application/pdf"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

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

export default function IngestionInput() {
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"file" | "text">("file");
  const { addJob, addTextJob } = useJobManager();

  async function onFileSubmit(values: z.infer<typeof fileSchema>) {
    setIsLoading(true);
    try {
      await addJob(values.file);
    } catch (error) {
      console.error("File ingestion failed:", error);
      toast.error("Failed to ingest file");
    } finally {
      setIsLoading(false);
    }
  }

  async function onTextSubmit(values: z.infer<typeof textSchema>) {
    setIsLoading(true);
    try {
      await addTextJob(values.text);
    } catch (error) {
      console.error("Text ingestion failed:", error);
      toast.error("Failed to ingest text");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl w-full space-y-4 flex flex-col items-center justify-center h-full">
      <Card className="mx-auto w-full h-1/2">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold tracking-tight">
            Create Tasks
          </CardTitle>
          <CardDescription>
            Upload a file or paste text to extract tasks automatically
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col h-full">
          <Tabs
            value={activeTab}
            onValueChange={(v) => setActiveTab(v as "file" | "text")}
            className="flex-1 flex flex-col"
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="file">
                <Upload className="mr-2 w-4 h-4" />
                Upload File
              </TabsTrigger>
              <TabsTrigger value="text">
                <FileText className="mr-2 w-4 h-4" />
                Enter Text
              </TabsTrigger>
            </TabsList>
            <TabsContent value="file" className="mt-4 flex-1 flex flex-col">
              <FileInput onSubmit={onFileSubmit} isLoading={isLoading} />
            </TabsContent>
            <TabsContent value="text" className="mt-4 flex-1 flex flex-col">
              <TextInput onSubmit={onTextSubmit} isLoading={isLoading} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

function FileInput({
  onSubmit,
  isLoading,
}: {
  onSubmit: (values: z.infer<typeof fileSchema>) => void;
  isLoading: boolean;
}) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const fileForm = useForm<z.infer<typeof fileSchema>>({
    resolver: zodResolver(fileSchema),
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleBrowseFiles = () => {
    fileInputRef.current?.click();
  };

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
    <Form {...fileForm}>
      <form
        onSubmit={fileForm.handleSubmit(onSubmit)}
        className="space-y-4 flex flex-col flex-1 w-full h-full"
      >
        <FormField
          control={fileForm.control}
          name="file"
          render={({ field: { onChange, ...fieldProps } }) => (
            <FormItem className="w-full flex-1 flex flex-col">
              <FormLabel>Input File</FormLabel>
              <FormControl className="h-full">
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onClick={handleBrowseFiles}
                  className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer  w-full flex flex-col items-center justify-center h-full"
                >
                  {selectedFile ? (
                    <div className="flex flex-col items-center justify-center">
                      <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                      <div className="flex items-center gap-2">
                        <p className="text-sm text-muted-foreground">
                          Selected File:
                        </p>
                        <p className="text-sm">{selectedFile.name}</p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        className="mt-4"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleFileChange(null);
                          fileForm.reset();
                        }}
                      >
                        <X className="h-4 w-4" /> Clear Selection
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
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED_FILE_TYPES.join(",")}
                    className="hidden"
                    id="file-input"
                    name="file"
                    onBlur={fieldProps.onBlur}
                    disabled={fieldProps.disabled}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        handleFileChange(file);
                        onChange(file);
                      }
                    }}
                  />
                  <label htmlFor="file-input" className="cursor-pointer">
                    {!selectedFile && (
                      <Button type="button" variant="outline" className="mt-4">
                        Browse Files
                      </Button>
                    )}
                  </label>
                </div>
              </FormControl>
            </FormItem>
          )}
        />

        <Button
          type="submit"
          disabled={!selectedFile || isLoading}
          className="w-1/2 mx-auto"
        >
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Spinner /> Analyzing...
            </div>
          ) : (
            "Analyze File"
          )}
        </Button>
      </form>
    </Form>
  );
}

function TextInput({
  onSubmit,
  isLoading,
}: {
  onSubmit: (values: z.infer<typeof textSchema>) => void;
  isLoading: boolean;
}) {
  const textForm = useForm<z.infer<typeof textSchema>>({
    resolver: zodResolver(textSchema),
    defaultValues: {
      text: "",
    },
  });
  return (
    <Form {...textForm}>
      <form
        onSubmit={textForm.handleSubmit(onSubmit)}
        className="space-y-4 flex flex-col flex-1 w-full"
      >
        <FormField
          control={textForm.control}
          name="text"
          render={({ field }) => (
            <FormItem className="w-full flex-1 flex flex-col">
              <FormLabel>Input Text</FormLabel>
              <FormControl className="flex-1 flex flex-col">
                <div className="border-2 rounded-lg hover:border-primary transition-colors min-h-[250px] w-full flex-1 flex flex-col">
                  <Textarea
                    {...field}
                    placeholder="Enter your text here..."
                    className="flex-1 min-h-[200px] w-full resize-none border-0 focus-visible:ring-0 focus-visible:ring-offset-0 shadow-none overflow-y-auto break-words whitespace-pre-wrap"
                  />
                </div>
              </FormControl>
            </FormItem>
          )}
        />

        <Button
          type="submit"
          disabled={!textForm.formState.isValid || isLoading}
          className="w-1/2 mx-auto"
        >
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Spinner /> Analyzing...
            </div>
          ) : (
            "Analyze Text"
          )}
        </Button>
      </form>
    </Form>
  );
}
