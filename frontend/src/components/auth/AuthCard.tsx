import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import Link from "next/link";

interface AuthCardProps {
  title: string;
  description: string;
  children: React.ReactNode;
  footerText: string;
  footerLinkText: string;
  footerLinkHref: string;
}

export function AuthCard({
  title,
  description,
  children,
  footerText,
  footerLinkText,
  footerLinkHref,
}: AuthCardProps) {
  return (
    <div className="flex min-h-screen w-full items-center justify-center p-4 bg-gray-50">
      <Card className="mx-auto max-w-sm w-full border-none shadow-none sm:border sm:shadow-sm">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold tracking-tight">
            {title}
          </CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          {children}
          <div className="mt-4 text-center text-sm">
            {footerText}{" "}
            <Link
              href={footerLinkHref}
              className="underline underline-offset-4 font-medium"
            >
              {footerLinkText}
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
