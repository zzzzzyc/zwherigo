using System.Reflection;
using System.Text.Json;

internal sealed class BridgeRequest
{
    public string lua_path { get; set; } = "";
    public string output_gwc { get; set; } = "";
    public string cartridge_id { get; set; } = "";
    public string player_name { get; set; } = "Builder";
    public string user_name { get; set; } = "builder";
    public string device_type { get; set; } = "PPC2003";
    public string engine_version { get; set; } = "V0210";
    public string? zoneslinker_dll { get; set; }
}

internal static class Program
{
    private static int Main(string[] args)
    {
        try
        {
            var requestJson = ReadRequestJson(args);
            var request = JsonSerializer.Deserialize<BridgeRequest>(requestJson);
            if (request is null)
            {
                return PrintError("Invalid request payload.");
            }

            ValidateRequest(request);
            var outputFile = Compile(request);
            Console.Out.WriteLine(
                JsonSerializer.Serialize(
                    new { ok = true, output_gwc = outputFile, compiler = "legacy-bridge" }
                )
            );
            return 0;
        }
        catch (Exception ex)
        {
            return PrintError(ex.Message);
        }
    }

    private static string ReadRequestJson(string[] args)
    {
        for (var i = 0; i < args.Length; i++)
        {
            if (args[i] == "--request-json" && i + 1 < args.Length)
            {
                return args[i + 1];
            }
        }
        throw new InvalidOperationException("Missing --request-json argument.");
    }

    private static void ValidateRequest(BridgeRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.lua_path))
        {
            throw new InvalidOperationException("lua_path is required.");
        }
        if (string.IsNullOrWhiteSpace(request.output_gwc))
        {
            throw new InvalidOperationException("output_gwc is required.");
        }
        if (!File.Exists(request.lua_path))
        {
            throw new FileNotFoundException($"Lua file not found: {request.lua_path}");
        }
    }

    private static string Compile(BridgeRequest request)
    {
        var linkerPath = ResolveZonesLinkerDll(request);
        var assembly = Assembly.LoadFrom(linkerPath);
        var linkerType = assembly.GetType("Groundspeak.Wherigo.ZonesLinker.ZonesLinker");
        if (linkerType is null)
        {
            throw new InvalidOperationException("Could not locate ZonesLinker type.");
        }

        var createMethod = linkerType.GetMethod("CreateZonesFile");
        if (createMethod is null)
        {
            throw new InvalidOperationException("Could not locate CreateZonesFile method.");
        }

        var deviceType = ParseEnumValue(assembly, "Groundspeak.Wherigo.ZonesLinker.DeviceType", request.device_type);
        var engineVersion = ParseEnumValue(
            assembly,
            "Groundspeak.Wherigo.ZonesLinker.EngineVersion",
            request.engine_version
        );

        var linker = Activator.CreateInstance(linkerType);
        if (linker is null)
        {
            throw new InvalidOperationException("Could not instantiate ZonesLinker.");
        }

        var outputDir = Path.GetDirectoryName(Path.GetFullPath(request.output_gwc));
        if (!string.IsNullOrWhiteSpace(outputDir))
        {
            Directory.CreateDirectory(outputDir);
        }

        createMethod.Invoke(
            linker,
            new object?[]
            {
                Path.GetFullPath(request.lua_path),
                Path.GetFullPath(request.output_gwc),
                request.cartridge_id,
                request.player_name,
                -1L,
                request.user_name,
                deviceType,
                engineVersion
            }
        );

        if (!File.Exists(request.output_gwc))
        {
            throw new InvalidOperationException($"Expected output file not created: {request.output_gwc}");
        }
        return Path.GetFullPath(request.output_gwc);
    }

    private static object ParseEnumValue(Assembly assembly, string enumTypeName, string enumValue)
    {
        var enumType = assembly.GetType(enumTypeName);
        if (enumType is null)
        {
            throw new InvalidOperationException($"Could not find enum type: {enumTypeName}");
        }
        try
        {
            return Enum.Parse(enumType, enumValue, ignoreCase: true);
        }
        catch
        {
            var names = string.Join(", ", Enum.GetNames(enumType));
            throw new InvalidOperationException(
                $"Invalid enum value '{enumValue}' for {enumTypeName}. Expected one of: {names}"
            );
        }
    }

    private static string ResolveZonesLinkerDll(BridgeRequest request)
    {
        if (!string.IsNullOrWhiteSpace(request.zoneslinker_dll))
        {
            var explicitPath = Path.GetFullPath(request.zoneslinker_dll);
            if (File.Exists(explicitPath))
            {
                return explicitPath;
            }
            throw new FileNotFoundException($"zoneslinker_dll not found: {explicitPath}");
        }

        var localPath = Path.Combine(AppContext.BaseDirectory, "ZonesLinker.dll");
        if (File.Exists(localPath))
        {
            return localPath;
        }

        throw new FileNotFoundException(
            "ZonesLinker.dll not found. Provide zoneslinker_dll in request JSON or place DLL beside bridge executable."
        );
    }

    private static int PrintError(string error)
    {
        Console.Error.WriteLine(JsonSerializer.Serialize(new { ok = false, error }));
        return 1;
    }
}
