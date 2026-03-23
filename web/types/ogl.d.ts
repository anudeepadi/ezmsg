declare module "ogl" {
  export class Renderer {
    gl: WebGLRenderingContext & { canvas: HTMLCanvasElement };
    constructor(options?: { alpha?: boolean; [key: string]: unknown });
    setSize(width: number, height: number): void;
    render(options: { scene: Mesh }): void;
  }

  export class Program {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    uniforms: Record<string, { value: any }>;
    constructor(
      gl: WebGLRenderingContext,
      options: {
        vertex: string;
        fragment: string;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        uniforms?: Record<string, { value: any }>;
      },
    );
  }

  export class Mesh {
    constructor(
      gl: WebGLRenderingContext,
      options: { geometry: Triangle; program: Program },
    );
  }

  export class Triangle {
    constructor(gl: WebGLRenderingContext);
  }

  export class Color {
    r: number;
    g: number;
    b: number;
    constructor(r?: number, g?: number, b?: number);
  }
}
