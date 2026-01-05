import re
import yaml
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os


def parse_chart(chart_file)
    with open(chart_file, r, encoding=utf-8, errors=ignore) as f
        lines = f.readlines()

    bpm_changes = []
    notes = []
    resolution = 192  # pasos por negra en .chart (típico GH)

    for line in lines
        # BPM (Ticks - Bpm)
        if B in line and = in line
            match = re.match(r(d+) = B (d+), line.strip())
            if match
                tick, bpm_val = map(int, match.groups())
                bpm = 60000000  bpm_val  # microsegundos → BPM real
                bpm_changes.append((tick, bpm))

        # Nota (Ticks - Lane, duración)
        if N in line and = in line
            match = re.match(r(d+) = N (d+) (d+), line.strip())
            if match
                tick, lane, length = map(int, match.groups())
                end_tick = tick + length if length  0 else None
                notes.append((tick, lane, end_tick))

    bpm_changes.sort(key=lambda x x[0])  # ordenar por tick
    return bpm_changes, notes, resolution


def ticks_to_ms(tick, bpm_changes, resolution)
    
    Convierte ticks acumulando el tiempo en ms según cada sección de BPM.
    
    ms_time = 0
    last_tick = 0
    last_bpm = bpm_changes[0][1]

    for i, (bpm_tick, bpm_val) in enumerate(bpm_changes)
        if tick  bpm_tick
            break
        # tiempo transcurrido hasta este cambio de BPM
        ms_per_tick = (60000  last_bpm)  resolution
        ms_time += (bpm_tick - last_tick)  ms_per_tick
        last_tick = bpm_tick
        last_bpm = bpm_val

    # tiempo desde último BPM hasta el tick
    ms_per_tick = (60000  last_bpm)  resolution
    ms_time += (tick - last_tick)  ms_per_tick

    return round(ms_time, 3)


def convert_to_qua(chart_file, audio_file, output_zip, metadata)
    bpm_changes, notes, resolution = parse_chart(chart_file)

    qua_data = {
        AudioFile os.path.basename(audio_file),
        SongPreviewTime 0,
        BackgroundFile ,
        MapId 1,
        MapSetId 1,
        Mode Keys4,
        Title metadata.get(title, Unknown),
        Artist metadata.get(artist, Unknown),
        Source metadata.get(source, ),
        Tags metadata.get(tags, ),
        Creator metadata.get(creator, Chart2Qua),
        DifficultyName metadata.get(difficulty, Expert),
        Description metadata.get(description, ),
        TimingPoints [],
        SliderVelocities [],
        HitObjects []
    }

    # Guardar TimingPoints en ms
    for tick, bpm in bpm_changes
        qua_data[TimingPoints].append({
            StartTime ticks_to_ms(tick, bpm_changes, resolution),
            Bpm bpm
        })

    # Mapear 5K - 4K
    lane_map = {0 1, 1 2, 2 3, 3 4, 4 2}  # el lane 4 se recicla a la mitad

    # Convertir notas a ms
    for start_tick, lane, end_tick in notes
        if lane not in lane_map
            continue
        hitobj = {
            StartTime ticks_to_ms(start_tick, bpm_changes, resolution),
            Lane lane_map[lane]
        }
        if end_tick
            hitobj[EndTime] = ticks_to_ms(end_tick, bpm_changes, resolution)
        qua_data[HitObjects].append(hitobj)

    # Guardar .qua temporal
    qua_file = song.qua
    with open(qua_file, w, encoding=utf-8) as f
        yaml.dump(qua_data, f, sort_keys=False)

    # Crear .zip
    with zipfile.ZipFile(output_zip, w) as zipf
        zipf.write(qua_file)
        zipf.write(audio_file, os.path.basename(audio_file))

    os.remove(qua_file)


def run_gui()
    root = tk.Tk()
    root.withdraw()

    # Seleccionar .chart
    chart_file = filedialog.askopenfilename(
        title=Selecciona el archivo .chart,
        filetypes=[(Chart Files, .chart)]
    )
    if not chart_file
        messagebox.showerror(Error, No seleccionaste un archivo .chart)
        return

    # Seleccionar .mp3
    audio_file = filedialog.askopenfilename(
        title=Selecciona el archivo de audio (.mp3),
        filetypes=[(MP3 Files, .mp3)]
    )
    if not audio_file
        messagebox.showerror(Error, No seleccionaste un archivo de audio)
        return

    # Pedir metadatos
    metadata = {}
    metadata[title] = simpledialog.askstring(Metadatos, Título de la canción, initialvalue=Unknown)
    metadata[artist] = simpledialog.askstring(Metadatos, Artista, initialvalue=Unknown)
    metadata[creator] = simpledialog.askstring(Metadatos, Creador del mapa, initialvalue=Chart2Qua)
    metadata[difficulty] = simpledialog.askstring(Metadatos, Nombre de la dificultad, initialvalue=Expert)
    metadata[source] = simpledialog.askstring(Metadatos, Fuente, initialvalue=)
    metadata[tags] = simpledialog.askstring(Metadatos, Tags, initialvalue=)
    metadata[description] = simpledialog.askstring(Metadatos, Descripción, initialvalue=)

    # Seleccionar salida .zip
    output_zip = filedialog.asksaveasfilename(
        title=Guardar como,
        defaultextension=.zip,
        filetypes=[(Zip Files, .zip)]
    )
    if not output_zip
        messagebox.showerror(Error, No seleccionaste un nombre de salida)
        return

    # Convertir
    convert_to_qua(chart_file, audio_file, output_zip, metadata)
    messagebox.showinfo(Éxito, fConversión completada!nArchivo guardado en {output_zip})


if __name__ == __main__
    run_gui()