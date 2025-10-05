import { Button } from "@/components/ui/button"
import { ArrowRight, CloudUpload, Sparkles, Zap } from "lucide-react"

export default function ComponentLibrary() {
  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
        CloudCommerce UI Components
      </h1>
      
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-6">Buttons</h2>
        <div className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Primary Buttons</h3>
            <div className="flex flex-wrap gap-4 items-center">
              <Button>Default</Button>
              <Button variant="default" size="lg">
                Get Started <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <Button variant="default" size="sm">
                Small
              </Button>
              <Button disabled>Disabled</Button>
              <Button isLoading>Loading</Button>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-medium">Secondary Buttons</h3>
            <div className="flex flex-wrap gap-4 items-center">
              <Button variant="secondary">Secondary</Button>
              <Button variant="secondary" size="lg">
                <CloudUpload className="mr-2 h-4 w-4" /> Upload
              </Button>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-medium">Special Buttons</h3>
            <div className="flex flex-wrap gap-4 items-center">
              <Button variant="premium">
                <Sparkles className="mr-2 h-4 w-4" />
                Premium Feature
              </Button>
              <Button variant="ai">
                <Zap className="mr-2 h-4 w-4" />
                AI Analysis
              </Button>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-medium">Outline Buttons</h3>
            <div className="flex flex-wrap gap-4 items-center">
              <Button variant="outline">Outline</Button>
              <Button variant="outline" size="lg">
                Large Outline
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="mb-12 p-6 bg-slate-50 dark:bg-slate-900 rounded-lg">
        <h2 className="text-2xl font-semibold mb-6">Call to Action</h2>
        <div className="text-center
```
